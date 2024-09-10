from django.db import models
from datetime import datetime
#from BagTracker.authorization.models import User

class Status(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    number = models.IntegerField(null=False, blank=False)

    def __str__(self):
        return self.name

class Priority(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)

    def __str__(self):
        return self.name

class Task(models.Model):
    type = models.CharField(max_length=255, null=False, blank=False)
    priority = models.ForeignKey(Priority, on_delete=models.CASCADE, related_name='tasks')
    status = models.ForeignKey(Status, on_delete=models.CASCADE, related_name='tasks')
    header = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    executor = models.ForeignKey('authorization.User', on_delete=models.CASCADE, related_name='executed_tasks', null=True)
    creator = models.ForeignKey('authorization.User', on_delete=models.CASCADE, related_name='created_tasks', null=False)
    date_creation = models.DateTimeField(default=datetime.now, null=False, blank=False)
    date_change = models.DateTimeField(auto_now=True, null=False, blank=False)

    def __str__(self):
        return self.header

class TaskHistory(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='history')
    type = models.CharField(max_length=255, null=False, blank=False)
    priority = models.ForeignKey(Priority, on_delete=models.CASCADE, null=True)
    status = models.ForeignKey(Status, on_delete=models.CASCADE, null=False)
    header = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    executor = models.ForeignKey('authorization.User', on_delete=models.CASCADE, related_name='task_history_executor', null=True)
    date_change = models.DateTimeField(default=datetime.now, null=False, blank=False)
    user = models.ForeignKey('authorization.User', on_delete=models.CASCADE, related_name='task_history_user', null=False)

    def __str__(self):
        return f"{self.task.header} - {self.date_change}"

class Execution(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    user = models.ForeignKey('authorization.User', on_delete=models.CASCADE)
