from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect

def login_view(request):
    if request.method == 'POST':
        login_name = request.POST.get('login')
        password = request.POST.get('password')

        user = authenticate(request, username=login_name, password=password)
        if user is not None:
            login(request, user)
            return redirect('tasks')
        else:
            context = {'error': 'Неверный логин или пароль'}
            return render(request, 'login.html', context)

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'dashboard.html', {'user': request.user})

from django.contrib.auth.models import User
from django.shortcuts import render, redirect

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            return redirect('login')
        except:
            context = {'error': 'Не удалось создать пользователя'}
            return render(request, 'register.html', context)

    return render(request, 'register.html')


