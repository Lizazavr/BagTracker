# BugTracker

BugTracker - веб-приложение для отслеживания выполнения задач.

## Запуск приложения

### Создание завизимостей

poetry install

### Запуск сервера

poetry run python manage.py runserver

### Запуск тестов

poetry manager.py test tasks

### Создание и запуск миграций

poetry manager.py makemigrations
poetry manager.py migrate

### Проверка покрытия тестов

coverage run --source=tasks manage.py test tasks
coverage html

После выполнения последней команды, отчет о покрытии тестов будет доступен по пути:

BagTracker/BagTracker/htmlcov/index.html

## Аккаунт менеджера
- login: manager
- password: password
