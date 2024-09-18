import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BugTracker.settings")
import django
django.setup()
from rest_framework.exceptions import ErrorDetail
from django.test import TestCase
from django.utils import timezone
from datetime import datetime
from rest_framework.test import APIClient, APITestCase
from .models import TaskHistory, Subtasks, Dependency
from rest_framework.test import APITestCase
from .models import Task, TaskType, Priority, Status
from django.urls import reverse
from rest_framework import status
from django.contrib.auth.models import User, Group

class TaskListViewTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.task_type = TaskType.objects.create(name='Bug')
        self.task_type2 = TaskType.objects.create(name='Task')
        self.priority = Priority.objects.create(name='High')
        self.status = Status.objects.create(name='To do', number=1)
        self.task1 = Task.objects.create(
            type=self.task_type, priority=self.priority, status=self.status,
            header='Test task 1', description='This is a test task',
            executor=self.user, creator=self.user
        )
        self.task2 = Task.objects.create(
            type=self.task_type2, priority=self.priority, status=self.status,
            header='Test task 2', description='This is another test task',
            executor=self.user, creator=self.user
        )

    def test_task_list_view_with_authenticated_user(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('tasks')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertContains(response, self.task1.header)
        self.assertContains(response, self.task2.header)

    def test_task_list_view_with_status_filter(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('tasks') + '?status=To do'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertContains(response, self.task1.header)
        self.assertContains(response, self.task2.header)

    def test_task_list_view_with_priority_filter(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('tasks') + '?priority=High'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertContains(response, self.task1.header)
        self.assertContains(response, self.task2.header)

    def test_task_list_view_with_executor_filter(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('tasks') + '?executor=testuser'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertContains(response, self.task1.header)
        self.assertContains(response, self.task2.header)

    def test_task_list_view_with_creator_filter(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('tasks') + '?creator=testuser'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertContains(response, self.task1.header)
        self.assertContains(response, self.task2.header)

    def test_task_list_view_with_search_query(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('tasks') + '?search=Test'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertContains(response, self.task1.header)
        self.assertContains(response, self.task2.header)

    def test_task_list_view_with_type_query(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('tasks') + '?type=Task'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertContains(response, self.task2.header)

    def test_task_list_view_with_unauthenticated_user(self):
        url = reverse('tasks')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {'detail': 'Authentication credentials were not provided.'})

class TestTaskDetailView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        self.priority1 = Priority.objects.create(name='Low')
        self.status1 = Status.objects.create(name='To Do', number=1)
        self.creator1 = User.objects.create_user(username='creator1', password='pass1')
        self.type1 = TaskType.objects.create(name='bug')
        self.task_creation_date = datetime(2023, 4, 15, 10, 30, 0, tzinfo=timezone.get_current_timezone())

        self.task1 = Task.objects.create(
            header='Task 1',
            description='This is task 1',
            priority=self.priority1,
            status=self.status1,
            executor=self.user,
            creator=self.creator1,
            type_id=self.type1.id,
            date_creation=self.task_creation_date
        )

        self.task_history1 = TaskHistory.objects.create(
            task=self.task1,
            description='Task created',
            date_change=timezone.now(),
            status=self.status1,
            user=self.user,
        )

        self.task2 = Task.objects.create(
            header='Task 2',
            description='This is task 2',
            priority=self.priority1,
            status=self.status1,
            executor=self.user,
            creator=self.creator1,
            type_id=self.type1.id,
            date_creation=self.task_creation_date
        )

        self.task0 = Task.objects.create(
            header='Task 0',
            description='This is task 0',
            priority=self.priority1,
            status=self.status1,
            executor=self.user,
            creator=self.creator1,
            type_id=self.type1.id,
            date_creation=self.task_creation_date
        )

        self.subtask1 = Subtasks.objects.create(
            id_task=self.task1,
            id_subtask=self.task2
        )

        self.dependency1 = Dependency.objects.create(
            blocking_task=self.task1,
            blocked_task=self.task2
        )

        self.dependency2 = Dependency.objects.create(
            blocking_task=self.task0,
            blocked_task=self.task1
        )

    def test_task_detail_view_success(self):
        url = reverse('task_detail', args=[self.task1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        task_data = response.data['task']
        self.assertEqual(task_data['id'], self.task1.id)
        self.assertEqual(task_data['header'], self.task1.header)
        self.assertEqual(task_data['description'], self.task1.description)

        task_history_data = response.data['task_history']
        self.assertEqual(len(task_history_data), 1)
        self.assertEqual(task_history_data[0]['description'], self.task_history1.description)

        blocking_tasks_data = response.data['blocking_tasks']
        self.assertEqual(len(blocking_tasks_data), 1)
        self.assertEqual(blocking_tasks_data[0]['id'], self.task0.id)

        blocked_tasks_data = response.data['blocked_tasks']
        self.assertEqual(len(blocked_tasks_data), 1)
        self.assertEqual(blocked_tasks_data[0]['id'], self.task2.id)

        parent_task_data = response.data['parent_task']
        self.assertIsNone(parent_task_data)

        child_tasks_data = response.data['child_tasks']
        self.assertEqual(len(child_tasks_data), 1)
        self.assertEqual(child_tasks_data[0]['id'], self.task2.id)

    def test_task_detail_view_not_found(self):
        url = reverse('task_detail', args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class TaskCreateViewTestCase(APITestCase):
    def setUp(self):
        self.developer = User.objects.create_user(username='developer', password='password')
        self.developer.groups.add(Group.objects.create(name='Разработчик'))
        self.tester = User.objects.create_user(username='tester', password='password')
        self.tester.groups.add(Group.objects.create(name='Тест-инженер'))
        self.manager = User.objects.create_user(username='manager', password='password')
        self.manager.groups.add(Group.objects.create(name='Менеджер'))
        self.task_type = TaskType.objects.create(name='Bug')
        self.priority = Priority.objects.create(name='High')
        self.status_in_progress = Status.objects.create(name='In progress', number=2)
        self.status_testing = Status.objects.create(name='Testing', number=5)

    def test_task_create_view_with_valid_data(self):
        self.client.force_authenticate(user=self.developer)
        url = reverse('task_create') + '?type=Bug&priority=High&status=In progress&header=Test+task&description=This+is+a+test+task&executor=developer'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 1)
        self.assertEqual(response.data['header'], 'Test task')
        self.assertEqual(response.data['executor']['username'], 'developer')

    def test_task_create_view_with_missing_required_fields(self):
        self.client.force_authenticate(user=self.developer)
        url = reverse('task_create') + '?priority=High&status=In progress&header=Test+task&description=This+is+a+test+task&executor=developer'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'Обязательные поля не заполнены.'})

    def test_task_create_view_with_manager_as_executor(self):
        self.client.force_authenticate(user=self.developer)
        url = reverse('task_create') + '?type=Bug&priority=High&status=In progress&header=Test+task&description=This+is+a+test+task&executor=manager'
        response = self.client.post(url)


        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'Пользователь с ролью "менеджер" не может быть назначен исполнителем.'})

    def test_task_create_view_with_tester_as_executor_for_in_progress_status(self):
        self.client.force_authenticate(user=self.developer)
        url = reverse('task_create') + '?type=Bug&priority=High&status=In progress&header=Test+task&description=This+is+a+test+task&executor=tester'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.data, {'error': 'При статусах "In progress", "Code review", "Dev test" исполнителем не может быть тест-инженер.'})

    def test_task_create_view_with_developer_as_executor_for_testing_status(self):
        self.client.force_authenticate(user=self.tester)
        url = reverse('task_create') + '?type=Bug&priority=High&status=Testing&header=Test+task&description=This+is+a+test+task&executor=developer'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'При статусе "Testing" исполнителем не может быть разработчик.'})

class AssignRolesViewTestCase(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(username='manager', password='password')
        self.manager.groups.add(Group.objects.create(name='Менеджер'))
        self.regular_user = User.objects.create_user(username='regular_user', password='password')

    def test_assign_roles_view_with_authenticated_manager(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse('assign_roles')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), User.objects.count())

    def test_assign_roles_view_with_unauthenticated_user(self):
        url = reverse('assign_roles')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {'detail': 'Authentication credentials were not provided.'})

    def test_assign_roles_view_with_non_manager_user(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('assign_roles')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {'detail': 'You do not have permission to perform this action.'})

class UpdateRolesViewTestCase(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(username='manager', password='password')
        self.manager.groups.add(Group.objects.create(name='Менеджер'))
        self.regular_user = User.objects.create_user(username='regular_user', password='password')
        self.new_group = Group.objects.create(name='Тимлид')

    def test_update_roles_view_with_authenticated_manager(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse('update_roles', args=[self.regular_user.id, self.new_group.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('username', response.data)
        self.assertEqual(response.data['username'], self.regular_user.username)

    def test_update_roles_view_with_unauthenticated_user(self):
        url = reverse('update_roles', args=[self.regular_user.id, self.new_group.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {'detail': 'Authentication credentials were not provided.'})

    def test_update_roles_view_with_non_existent_user(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse('update_roles', args=[999, self.new_group.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'Неверный пользователь или роль'})

    def test_update_roles_view_with_non_existent_group(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse('update_roles', args=[self.regular_user.id, 999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'Неверный пользователь или роль'})

class UpdateTaskStatusViewTestCase(APITestCase):
    def setUp(self):
        self.developer = User.objects.create_user(username='developer', password='password')
        self.developer.groups.add(Group.objects.create(name='Разработчик'))
        self.tester = User.objects.create_user(username='tester', password='password')
        self.tester.groups.add(Group.objects.create(name='Тест-инженер'))
        self.task_type = TaskType.objects.create(name='Bug')
        self.priority = Priority.objects.create(name='High')
        self.task = Task.objects.create(
            header='Test Task',
            description='This is a test task',
            type=self.task_type,
            priority=self.priority,
            status=Status.objects.create(name='To do', number=1),
            executor=self.developer,
            creator=self.developer
        )

        self.task2 = Task.objects.create(
            header='Test Task',
            description='This is a test task',
            type=self.task_type,
            priority=self.priority,
            status=Status.objects.create(name='Dev test', number=4),
            executor=self.developer,
            creator=self.developer
        )

    def test_update_task_status_with_authenticated_non_manager_user(self):
        self.client.force_authenticate(user=self.developer)
        url = reverse('update_task_status', args=[self.task.id, Status.objects.create(name='In progress', number=2).id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status.name, 'In progress')
        self.assertEqual(self.task.executor, self.developer)

    def test_update_task_status_with_unauthenticated_user(self):
        url = reverse('update_task_status', args=[self.task.id, Status.objects.create(name='In progress', number=2).id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {'detail': 'Authentication credentials were not provided.'})

    def test_update_task_status_with_manager_user(self):
        manager = User.objects.create_user(username='manager', password='password')
        manager.groups.add(Group.objects.create(name='Менеджер'))
        self.client.force_authenticate(user=manager)
        url = reverse('update_task_status', args=[self.task.id, Status.objects.create(name='In progress', number=2).id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {'detail': 'You do not have permission to perform this action.'})

    def test_update_task_status_with_invalid_task_id(self):
        self.client.force_authenticate(user=self.developer)
        url = reverse('update_task_status', args=[999, Status.objects.create(name='In progress', number=2).id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_task_status_with_invalid_status_id(self):
        self.client.force_authenticate(user=self.developer)
        url = reverse('update_task_status', args=[self.task.id, 999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_task_status_with_tester_on_in_progress_status(self):
        self.client.force_authenticate(user=self.tester)
        url = reverse('update_task_status', args=[self.task.id, Status.objects.create(name='In progress', number=2).id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'success': False, 'error': 'При статусах "In progress", "Code review", "Dev test" исполнителем не может быть тест-инженер.'})

    def test_update_task_status_with_developer_on_testing_status(self):
        self.client.force_authenticate(user=self.developer)
        url = reverse('update_task_status', args=[self.task2.id, Status.objects.create(name='Testing', number=5).id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'success': False, 'error': 'При статусе "Testing" исполнителем не может быть разработчик.'})

class DeleteTaskViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(username='manager', password='password')
        self.manager.groups.add(Group.objects.create(name='Менеджер'))
        self.user = User.objects.create_user(username='user', password='password')
        self.task_type = TaskType.objects.create(name='Bug')
        self.priority = Priority.objects.create(name='High')
        self.status=Status.objects.create(name='To do', number=1)
        self.task1 = Task.objects.create(
            header='Test Task',
            description='This is a test task',
            type=self.task_type,
            priority=self.priority,
            status=self.status,
            creator=self.manager
        )

        self.task2 = Task.objects.create(
            header='Test Task2',
            description='This is a test task2',
            type=self.task_type,
            priority=self.priority,
            status=self.status,
            creator=self.manager
        )
        self.subtask = Subtasks.objects.create(id_task=self.task1, id_subtask=self.task2)
        self.dependency = Dependency.objects.create(blocking_task=self.task1, blocked_task=self.task2)
        self.task_history1 = TaskHistory.objects.create(
            task=self.task1,
            description='Task created',
            date_change=timezone.now(),
            status=self.status,
            user=self.user,
        )

    def test_delete_task_with_manager(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse('delete_task', args=[self.task1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.json(), {'success': True, 'error': 'Задача удалена'})
        self.assertFalse(Task.objects.filter(id=self.task1.id).exists())
        self.assertFalse(TaskHistory.objects.filter(task=self.task1).exists())
        self.assertFalse(Subtasks.objects.filter(id_task=self.task1).exists())
        self.assertFalse(Subtasks.objects.filter(id_subtask=self.task1).exists())
        self.assertFalse(Dependency.objects.filter(blocking_task=self.task1, blocked_task=self.task2).exists())

    def test_delete_task_with_non_manager(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('delete_task', args=[self.task1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {'detail': ErrorDetail(string='You do not have permission to perform this action.', code='permission_denied')})

    def test_delete_non_existent_task(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse('delete_task', args=[999])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': ErrorDetail(string='No Task matches the given query.', code='not_found')})


class ChangePasswordViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='oldpassword')

    def test_change_password_with_valid_input(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('change_password') + '?new_password=newpassword'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'Ваш пароль был успешно изменен.')

    def test_change_password_without_new_password(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('change_password')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error'], 'Новый пароль не указан.')

    def test_change_password_with_unauthenticated_user(self):
        url = reverse('change_password')
        response = self.client.post(url, {'new_password': 'newpassword'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_with_unsupported_method(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('change_password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': ErrorDetail(string='Method "GET" not allowed.', code='method_not_allowed')})

class ChangeUsernameViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(username='manager', password='password')
        self.manager.groups.add(Group.objects.create(name='Менеджер'))
        self.user = User.objects.create_user(username='testuser', password='password')

    def test_change_username_with_valid_input(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse('change_username', kwargs={'user_id': self.user.id})
        data = {'new_username': 'newusername'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'Ваш логин был успешно изменен.')
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'newusername')

    def test_change_username_with_existing_username(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse('change_username', kwargs={'user_id': self.user.id})
        data = {'new_username': self.manager.username}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error'], 'Этот логин уже занят.')

    def test_change_username_without_permission(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('change_username', kwargs={'user_id': self.user.id})
        response = self.client.post(url, {'new_username': 'newusername'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_username_for_non_existent_user(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse('change_username', kwargs={'user_id': 999})
        response = self.client.post(url, {'new_username': 'newusername'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error'], 'Пользователь не найден.')

class RegisterUserViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_user_with_valid_input(self):
        url = reverse('register_user', kwargs={'username': 'newuser', 'password': 'password123'})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'newuser')
        self.assertIn('token', response.data)

    def test_register_user_with_existing_username(self):
        User.objects.create_user(username='existinguser', password='password123')
        url = reverse('register_user', kwargs={'username': 'existinguser', 'password': 'password123'})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)

class UserLoginViewTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_user_login_with_valid_credentials(self):
        url = reverse('user_login', kwargs={'username': 'testuser', 'password': 'testpassword'})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)

    def test_user_login_with_invalid_username(self):
        url = reverse('user_login', kwargs={'username': 'invaliduser', 'password': 'testpassword'})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Неверный логин или пароль')

    def test_user_login_with_invalid_password(self):
        url = reverse('user_login', kwargs={'username': 'testuser', 'password': 'invalidpassword'})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Неверный логин ли пароль')



