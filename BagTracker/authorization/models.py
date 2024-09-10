from django.db import models

class Role(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)

    def __str__(self):
        return self.name

class User(models.Model):
    login = models.CharField(max_length=255, null=False, blank=False)
    password = models.CharField(max_length=255, null=False, blank=False)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='users')

    def __str__(self):
        return self.login
