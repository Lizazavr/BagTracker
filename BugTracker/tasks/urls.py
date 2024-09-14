from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path('tasks/detail/<int:task_id>/', views.task_detail_view, name='task_detail'),
    path('tasks/edit/<int:task_id>/', views.task_edit_view, name='task_edit'),
    path('tasks', views.task_list_view, name='tasks'),
    #path('tasks/detail', views.task_detail_view, name='task_detail'),
    path('tasks/create', views.task_create_view, name='task_create'),
    path('manager/assign_roles', views.assign_roles_view, name='assign_roles'),
    path('manager/update_roles/<int:user_id>/<int:group_id>', views.update_roles_view, name='update_roles'),
    path('manager/change_username/<int:user_id>/', views.change_username, name='change_username'),
    path('user/change_password/', views.change_password, name='change_password'),
    path('tasks/<int:task_id>/update_status/<int:status_id>/', views.update_task_status, name='update_task_status'),
    path('tasks/<int:task_id>/delete/', views.delete_task_view, name='delete_task'),
    path('user/register_user/<str:username>/<str:password>', views.register_user, name='register_user'),
    path('user/user_login/<str:username>/<str:password>', views.user_login, name='user_login'),
]

