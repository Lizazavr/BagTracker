# BugTracker

BugTracker - веб-приложение для отслеживания выполнения задач.

## Запуск приложения

### Создание завизимостей
```
poetry install
```
### Запуск сервера
```
poetry run python manage.py runserver
```
Сервер доступен по ссылке http://127.0.0.1:8000/api/docs

### Запуск тестов
```
poetry run python manage.py test tasks
```
### Создание и запуск миграций
```
poetry run python manage.py makemigrations
poetry run python manage.py migrate
```
### Проверка покрытия тестов
```
coverage run --source=tasks manage.py test tasks
coverage html
```
После выполнения последней команды, отчет о покрытии тестов будет доступен по пути:

BagTracker/BagTracker/htmlcov/index.html

## Аккаунт менеджера
- login: manager
- password: password
