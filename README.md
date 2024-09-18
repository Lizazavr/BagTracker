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
Для запуска тестов используйте локальную БД. Подключение к БД находится в файле BugTracker/settings.py.
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
poetry run coverage run --source=tasks manage.py test tasks
poetry run coverage html
```
После выполнения последней команды, отчет о покрытии тестов будет доступен по пути:

BagTracker/BagTracker/htmlcov/index.html

## Аккаунты
Менеджер:
- login: manager
- password: password

Тимлид:
- login: teamlead
- password: qwerty

Разработчик:
- login: developer
- password: 1234567890

Тест-инженер:
- login: test_engineer
- password: 123qwe456rty
