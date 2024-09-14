# BugTracker

BugTracker - веб-приложение для отслеживания выполнения задач.

## Запуск приложения

### Запуск тестов

python manager.py test tasks

### Запуск сервера

python manager.py runserver

### Создание и запуск миграций

python manager.py makemigrations
python manager.py migrate

### Проверка покрытия тестов

coverage run --source=tasks manage.py test tasks
coverage html

После выполнения последней команды, отчет о покрытии тестов будет доступен по пути:

BagTracker/BagTracker/htmlcov/index.html

## Аккаунт менеджера
- login: manager
- password: password
