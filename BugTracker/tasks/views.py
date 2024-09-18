from django.shortcuts import get_object_or_404
from .models import Task, Status, Priority, TaskHistory, Dependency, Subtasks, TaskType
from django.db.models import Q
from django.contrib.auth.models import Group, User
from django.db import transaction
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from .serializers import TaskSerializer, TaskHistorySerializer, UserSerializer, UserGroupSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, OpenApiTypes
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class IsManager(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user.is_authenticated:
            return user.groups.filter(name='Менеджер').exists()
        return False

class IsNotManager(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user.is_authenticated:
            return not user.groups.filter(name='Менеджер').exists()
        return True

# Функция отображения всех задач
@extend_schema(
    methods=['GET'],
    parameters=[
        OpenApiParameter('search', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY),
        OpenApiParameter('type', type=str, location=OpenApiParameter.QUERY, enum=[tasktype.name for tasktype in TaskType.objects.all()]),
        OpenApiParameter('executor', type=str, location=OpenApiParameter.QUERY, enum=[user.username for user in User.objects.all()]),
        OpenApiParameter('status', type=str, location=OpenApiParameter.QUERY, enum=[status.name for status in Status.objects.all()]),
        OpenApiParameter('creator', type=str, location=OpenApiParameter.QUERY, enum=[user.username for user in User.objects.all()]),
    ],
    responses={
        200: TaskSerializer(many=True),
    },
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def task_list_view(request):
    user = request.user

    status_filter = request.GET.get('status')
    type_filter = request.GET.get('type')
    executor_filter = request.GET.get('executor')
    creator_filter = request.GET.get('creator')
    search_query = request.GET.get('search')

    tasks = Task.objects.all().order_by('-date_change')

    if search_query:
        tasks = tasks.filter(
            Q(header__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(id__icontains=search_query)
        )

    if status_filter:
        tasks = tasks.filter(status__name=status_filter)
    if type_filter:
        tasks = tasks.filter(type__name=type_filter)
    if executor_filter:
        tasks = tasks.filter(executor__username=executor_filter)
    if creator_filter:
        tasks = tasks.filter(creator__username=creator_filter)

    serializer = TaskSerializer(tasks, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

# Функция отображения определенной задачи
@extend_schema(
    methods=['GET'],
    parameters=[
        OpenApiParameter('task_id', type=int, location=OpenApiParameter.PATH),
    ],
    responses={
        200: OpenApiResponse(response=TaskSerializer),
    },
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def task_detail_view(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task_history = TaskHistory.objects.filter(task=task).order_by('-id')

    parent_task_obj = Subtasks.objects.filter(id_subtask=task).first()
    if parent_task_obj:
        parent_task = parent_task_obj.id_task
    else:
        parent_task = None

    child_tasks = Task.objects.filter(
        id__in=Subtasks.objects.filter(id_task=task).values_list('id_subtask', flat=True))

    blocking_dependencies = Dependency.objects.filter(blocked_task=task)
    blocked_dependencies = Dependency.objects.filter(blocking_task=task)
    blocking_tasks = [dep.blocking_task for dep in blocking_dependencies]
    blocked_tasks = [dep.blocked_task for dep in blocked_dependencies]

    task_data = {
        'task': TaskSerializer(task).data,
        'task_history': TaskHistorySerializer(task_history, many=True).data,
        'blocking_tasks': [TaskSerializer(t).data for t in blocking_tasks],
        'blocked_tasks': [TaskSerializer(t).data for t in blocked_tasks],
        'parent_task': TaskSerializer(parent_task).data if parent_task else None,
        'child_tasks': [TaskSerializer(t).data for t in child_tasks],
    }

    return Response(task_data, status=status.HTTP_200_OK)

# Функция создания задачи
@extend_schema(
    methods=['POST'],
    parameters=[
        OpenApiParameter('type', type=str, location=OpenApiParameter.QUERY, enum=[task_type.name for task_type in TaskType.objects.all()], required=True),
        OpenApiParameter('priority', type=str, location=OpenApiParameter.QUERY, enum=[priority.name for priority in Priority.objects.all()]),
        OpenApiParameter('status', type=str, location=OpenApiParameter.QUERY, enum=[status.name for status in Status.objects.all()], required=True),
        OpenApiParameter('header', type=str, location=OpenApiParameter.QUERY, required=True),
        OpenApiParameter('description', type=str, location=OpenApiParameter.QUERY),
        OpenApiParameter('executor', type=str, location=OpenApiParameter.QUERY, enum=[user.username for user in User.objects.all()]),
        OpenApiParameter('parent_task', type=str, location=OpenApiParameter.QUERY, enum=[task.header for task in Task.objects.all()]),
        OpenApiParameter('blocked_tasks', type=str, location=OpenApiParameter.QUERY),
    ],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def task_create_view(request):
    type_name = request.query_params.get('type')
    priority_name = request.query_params.get('priority')
    status_name = request.query_params.get('status')
    header = request.query_params.get('header')
    description = request.query_params.get('description')
    executor_name = request.query_params.get('executor')

    if not all([type_name, status_name, header]):
        return Response({'error': 'Обязательные поля не заполнены.'}, status=status.HTTP_400_BAD_REQUEST)

    if executor_name:
        try:
            user = User.objects.get(username=executor_name)
            if user.groups.filter(name='Менеджер').exists():
                return Response({'error': 'Пользователь с ролью "менеджер" не может быть назначен исполнителем.'},
                                status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'Указанный исполнитель не найден.'}, status=status.HTTP_400_BAD_REQUEST)

    parent_task_header = request.query_params.get('parent_task')
    blocked_tasks_ids = [int(task_id.strip()) for task_id in request.query_params.get('blocked_tasks', '').split(',') if
                         task_id.strip()]

    type_obj = TaskType.objects.get(name=type_name)
    priority_obj = Priority.objects.get(name=priority_name) if priority_name else None
    status_obj = Status.objects.get(name=status_name)
    executor_obj = User.objects.get(username=executor_name) if executor_name else None
    parent_task_obj = Task.objects.get(header=parent_task_header) if parent_task_header else None

    if status_obj.name in ['In progress', 'Code review', 'Dev test'] and executor_obj and executor_obj.groups.filter(name='Тест-инженер').exists():
        return Response({'error': 'При статусах "In progress", "Code review", "Dev test" исполнителем не может быть тест-инженер.'}, status=status.HTTP_400_BAD_REQUEST)
    if status_obj.name == 'Testing' and executor_obj and executor_obj.groups.filter(name='Разработчик').exists():
        return Response({'error': 'При статусе "Testing" исполнителем не может быть разработчик.'}, status=status.HTTP_400_BAD_REQUEST)
    if status_obj.name == 'In progress' and not executor_obj:
            print(f'status', status_obj.name)
            return Response({'error': 'При статусе "In progress" обязательно должен быть назначен исполнитель.'}, status=status.HTTP_400_BAD_REQUEST)

    task = Task.objects.create(
        type=type_obj,
        priority=priority_obj,
        status=status_obj,

        header=header,
        description=description,
        creator=request.user,
    )

    if executor_obj:
        task.executor = executor_obj
        task.save()

    if parent_task_obj:
        Subtasks.objects.create(id_task=parent_task_obj, id_subtask=task)

    for blocked_task_id in blocked_tasks_ids:
        Dependency.objects.create(
            blocking_task_id=task.id,
            blocked_task_id=blocked_task_id
        )

    TaskHistory.objects.create(
        task_id=task.id,
        type=type_obj.id,
        priority_id=priority_obj.id if priority_obj else None,
        status_id=status_obj.id,
        header=header,
        description=description,
        executor_id=executor_obj.id if executor_obj else None,
        user_id=request.user.id,
    )

    return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)


# Функция редактирования задачи
@extend_schema(
    methods=['PUT'],
    parameters=[
        OpenApiParameter('task_id', type=int, location=OpenApiParameter.PATH, required=True),
        OpenApiParameter('type', type=str, location=OpenApiParameter.QUERY, enum=[task_type.name for task_type in TaskType.objects.all()], required=True),
        OpenApiParameter('priority', type=str, location=OpenApiParameter.QUERY, enum=[priority.name for priority in Priority.objects.all()]),
        OpenApiParameter('header', type=str, location=OpenApiParameter.QUERY, required=True),
        OpenApiParameter('description', type=str, location=OpenApiParameter.QUERY),
        OpenApiParameter('executor', type=str, location=OpenApiParameter.QUERY, enum=[user.username for user in User.objects.all()]),
        OpenApiParameter('blocked_tasks', type=str, location=OpenApiParameter.QUERY),
    ],
    responses={
        200: OpenApiResponse(response=TaskSerializer),
    },
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def task_edit_view(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    type_name = request.query_params.get('type')
    priority_name = request.query_params.get('priority')
    header = request.query_params.get('header')
    description = request.query_params.get('description')
    executor_name = request.query_params.get('executor')
    blocked_tasks_ids = [int(task_id.strip()) for task_id in request.query_params.get('blocked_tasks', '').split(',') if
                         task_id.strip()]

    if executor_name:
        try:
            user = User.objects.get(username=executor_name)
            if user.groups.filter(name='Менеджер').exists():
                return Response({'error': 'Пользователь с ролью "Менеджер" не может быть назначен исполнителем.'},
                                status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'Указанный исполнитель не найден.'}, status=status.HTTP_400_BAD_REQUEST)

    type_obj = TaskType.objects.get(name=type_name)
    priority_obj = Priority.objects.get(name=priority_name) if priority_name else None
    executor_obj = User.objects.get(username=executor_name) if executor_name else None

    task.type = type_obj
    task.priority = priority_obj
    task.header = header
    task.description = description
    task.executor = executor_obj
    task.save()

    Dependency.objects.filter(blocking_task=task).delete()
    Dependency.objects.filter(blocked_task=task).delete()

    for blocked_task_id in blocked_tasks_ids:
        Dependency.objects.create(
            blocking_task_id=task.id,
            blocked_task_id=blocked_task_id
        )

    TaskHistory.objects.create(
        task=task,
        type=type_obj,
        priority=priority_obj,
        status=task.status,
        header=header,
        description=description,
        executor=executor_obj,
        user=request.user
    )

    return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)


# Функция отображения всех пользователей
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsManager])
@extend_schema(
    methods=['POST'],
    responses={
        200: OpenApiResponse(description='List of users'),
        400: OpenApiResponse(description='Bad request'),
    },
)
def assign_roles_view(request):
    if request.method == 'POST':
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response({'error': 'Bad request'}, status=status.HTTP_400_BAD_REQUEST)


# Функция изменения роли пользователя
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsManager])
@extend_schema(
    methods=['POST'],
    parameters=[
        OpenApiParameter('user_id', type=int, location=OpenApiParameter.PATH, required=True),
        OpenApiParameter('group_id', type=int, location=OpenApiParameter.PATH, required=True),
    ],
)
def update_roles_view(request, user_id, group_id):
    try:
        user = User.objects.get(id=user_id)
        group = Group.objects.get(id=group_id)
    except (User.DoesNotExist, Group.DoesNotExist):
        return Response({'error': 'Неверный пользователь или роль'}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        user.groups.clear()
        user.groups.add(group)

    user_serializer = UserSerializer(user)
    user_group_serializer = UserGroupSerializer(user.groups.first())
    response_data = {**user_serializer.data, **user_group_serializer.data}
    return Response(response_data, status=status.HTTP_200_OK)


# Функция изменения статуса задачи
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsNotManager])
@extend_schema(
    methods=['POST'],
    parameters=[
        OpenApiParameter('task_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, required=True),
        OpenApiParameter('status_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, required=True),
    ],
    responses={
        200: OpenApiResponse(description='Успешно обновлено'),
        400: OpenApiResponse(description='Неверный статус'),
    },
)
def update_task_status(request, task_id, status_id):
    task = get_object_or_404(Task, pk=task_id)
    new_status = get_object_or_404(Status, pk=status_id)

    if task.priority:
        priority_id = task.priority.id
    else:
        priority_id = None

    if new_status.number == task.status.number + 1 or new_status.number in [0, 1]:
        if new_status.name in ['In progress', 'Code review', 'Dev test'] and request.user and request.user.groups.filter(name='Тест-инженер').exists():
            return JsonResponse({'success': False, 'error': 'При статусах "In progress", "Code review", "Dev test" исполнителем не может быть тест-инженер.'}, status=400)
        if new_status.name == 'Testing' and request.user and request.user.groups.filter(name='Разработчик').exists():
            return JsonResponse({'success': False, 'error': 'При статусе "Testing" исполнителем не может быть разработчик.'}, status=400)

        TaskHistory.objects.create(
            task=task,
            type=task.type.id,
            priority_id=priority_id,
            status=new_status,
            header=task.header,
            description=task.description,
            executor=request.user,
            user=request.user
        )

        task.status = new_status
        task.executor = request.user
        task.save()

        serializer = TaskSerializer(task)
        return JsonResponse(serializer.data, status=200)
    else:
        return JsonResponse({'success': False, 'error': 'Недопустимый статус'}, status=400)


# Функция удаления задачи
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsManager])
@extend_schema(
    methods=['DELETE'],
    parameters=[
        OpenApiParameter('task_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, required=True),
    ],
)
def delete_task_view(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    with transaction.atomic():
        TaskHistory.objects.filter(task=task).delete()
        Subtasks.objects.filter(id_task=task).delete()
        Subtasks.objects.filter(id_subtask=task).delete()
        Dependency.objects.filter(blocking_task=task).delete()
        Dependency.objects.filter(blocked_task=task).delete()
        task.delete()

    return JsonResponse({'success': True, 'error': 'Задача удалена'}, status=200)


# Функция изменения пароля
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@extend_schema(
    methods=['POST'],
    parameters=[
        OpenApiParameter('new_password', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY),
    ],
)
def change_password_view(request):
    if request.method == 'POST':
        new_password = request.query_params.get('new_password')
        if not new_password:
            return Response({'success': False, 'error': 'Новый пароль не указан.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'success': True, 'message': 'Ваш пароль был успешно изменен.'}, status=status.HTTP_200_OK)
    else:
        return Response({'success': False, 'error': 'Метод не поддерживается.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


# Функция изменения имени пользователя
@extend_schema(
    methods=['POST'],
    parameters=[
        OpenApiParameter('new_username', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY),
        OpenApiParameter('user_id', type=OpenApiTypes.STR, location=OpenApiParameter.PATH),
    ],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsManager])
def change_username_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'success': False, 'error': 'Пользователь не найден.'}, status=status.HTTP_404_NOT_FOUND)

    new_username = request.data.get('new_username')

    if not new_username:
        return Response({'success': False, 'error': 'Новый логин не может быть пустым.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=new_username).exclude(id=user.id).exists():
        return Response({'success': False, 'error': 'Этот логин уже занят.'}, status=status.HTTP_400_BAD_REQUEST)

    user.username = new_username
    user.save()

    return Response({'success': True, 'message': 'Ваш логин был успешно изменен.'}, status=status.HTTP_200_OK)


# Функция регистрации
@api_view(['POST'])
@extend_schema(
    methods=['POST'],
)
def register_user_view(request, username, password):
    if not username or not password:
        return Response({'error': 'Нет логина или пароля.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = User.objects.create_user(username=username, password=password)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'username': user.username, 'token': token.key}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Функция входа
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING),
            'password': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={
        '200': openapi.Response('Success', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'access_token': openapi.Schema(type=openapi.TYPE_STRING)
            }
        )),
        '400': openapi.Response('Bad Request')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def user_login_view(request, username, password):
    try:
        user = User.objects.get(username=username)
        if user.check_password(password):
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            return Response({'access_token': access_token})
        else:
            return Response({'error': 'Неверный логин ли пароль'}, status=400)
    except User.DoesNotExist:
        return Response({'error': 'Неверный логин или пароль'}, status=400)



