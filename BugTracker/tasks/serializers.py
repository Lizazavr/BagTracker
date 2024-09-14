from rest_framework import serializers
from .models import Status, TaskType, Task, TaskHistory, Execution, Dependency, Subtasks
from .models import Priority
from django.contrib.auth.models import User, Group

class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = ('id', 'name', 'number')

class PrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Priority
        fields = ('id', 'name')

class TaskTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskType
        fields = ('id', 'name')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')

class UserGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']


class TaskSerializer(serializers.ModelSerializer):
    type = TaskTypeSerializer(read_only=True)
    priority = PrioritySerializer(read_only=True)
    status = StatusSerializer(read_only=True)
    executor = UserSerializer(read_only=True)
    creator = UserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = ('id', 'type', 'priority', 'status', 'header', 'description', 'executor', 'creator', 'date_creation', 'date_change')

class TaskHistorySerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)
    priority = PrioritySerializer(read_only=True)
    status = StatusSerializer(read_only=True)
    executor = UserSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = TaskHistory
        fields = ('id', 'task', 'type', 'priority', 'status', 'header', 'description', 'executor', 'date_change', 'user')

class ExecutionSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Execution
        fields = ('id', 'task', 'user')

class DependencySerializer(serializers.ModelSerializer):
    blocking_task = TaskSerializer(read_only=True)
    blocked_task = TaskSerializer(read_only=True)

    class Meta:
        model = Dependency
        fields = ('id', 'blocking_task', 'blocked_task')

class SubtasksSerializer(serializers.ModelSerializer):
    id_task = TaskSerializer(read_only=True)
    id_subtask = TaskSerializer(read_only=True)

    class Meta:
        model = Subtasks
        fields = ('id', 'id_task', 'id_subtask')
