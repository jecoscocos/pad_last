# Testing Guide

## Обзор

Проект использует комплексную систему тестирования для обеспечения качества кода и стабильности микросервисов.

## Структура тестов

Каждый микросервис имеет собственный файл тестов:
- `auth-service/test_auth.py` - тесты аутентификации
- `property-service/test_property.py` - тесты управления недвижимостью
- `notification-service/test_notification.py` - тесты уведомлений
- `analytics-service/test_analytics.py` - тесты аналитики

## Запуск тестов

### Локальный запуск

#### Все тесты для одного сервиса:
```bash
cd microservices/auth-service
python -m pytest test_auth.py -v
```

#### С покрытием кода:
```bash
python -m pytest test_auth.py -v --cov=app --cov-report=html
```

#### Конкретный тест:
```bash
python -m pytest test_auth.py::TestAuthService::test_register_success -v
```

### Запуск всех тестов проекта:

```bash
# Windows PowerShell
Get-ChildItem -Path microservices -Recurse -Filter "test_*.py" | ForEach-Object {
    Push-Location $_.Directory
    python -m pytest $_.Name -v
    Pop-Location
}
```

### Запуск в Docker:

```bash
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## CI/CD Pipeline

### GitHub Actions

Pipeline автоматически запускается при:
- Push в ветки `main` или `develop`
- Создании Pull Request

Этапы:
1. **Test** - запуск unit-тестов для всех сервисов
2. **Lint** - проверка качества кода (flake8, black)
3. **Build** - сборка Docker образов
4. **Security Scan** - проверка уязвимостей (Trivy)
5. **Deploy** - развертывание (только для main)

### Настройка secrets в GitHub:

Необходимо добавить в Settings → Secrets and variables → Actions:
- `DOCKER_USERNAME` - логин Docker Hub
- `DOCKER_PASSWORD` - пароль Docker Hub
- `DEPLOY_HOST` - адрес сервера для деплоя
- `DEPLOY_USER` - пользователь SSH
- `DEPLOY_SSH_KEY` - приватный ключ SSH

## Покрытие кода

Целевое покрытие: **80%+**

Текущее покрытие по сервисам:
- auth-service: проверяется
- property-service: проверяется
- notification-service: проверяется
- analytics-service: проверяется

Просмотр отчета:
```bash
cd microservices/auth-service
python -m pytest --cov=app --cov-report=html
# Откройте htmlcov/index.html в браузере
```

## Типы тестов

### Unit Tests
Тестируют отдельные компоненты в изоляции:
- API endpoints
- Модели данных
- Бизнес-логика
- Валидация данных

### Integration Tests (планируется)
Тестируют взаимодействие сервисов:
- Межсервисное общение
- Сквозные сценарии (end-to-end)
- Работа с реальной БД

### Структура unit-теста:

```python
import unittest
from app import app, db

class TestAuthService(unittest.TestCase):
    def setUp(self):
        """Подготовка перед каждым тестом"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Очистка после каждого теста"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_example(self):
        """Тестовый метод"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
```

## Лучшие практики

1. **Изоляция тестов**: каждый тест должен быть независимым
2. **Понятные названия**: `test_register_success`, `test_login_wrong_password`
3. **Arrange-Act-Assert**: подготовка → действие → проверка
4. **Тестирование граничных случаев**: пустые данные, максимальные значения
5. **Мокирование внешних зависимостей**: использовать mock для HTTP запросов

## Отладка тестов

### Вывод дополнительной информации:
```bash
python -m pytest test_auth.py -v -s
```

### Остановка на первом провале:
```bash
python -m pytest test_auth.py -x
```

### Запуск только упавших тестов:
```bash
python -m pytest --lf
```

## Метрики качества

### Обязательные проверки:
- ✅ Все тесты проходят
- ✅ Покрытие кода > 80%
- ✅ Нет ошибок flake8
- ✅ Код отформатирован black
- ✅ Нет критических уязвимостей

### Рекомендуемые:
- Code complexity < 10 (flake8 --max-complexity=10)
- Документация для публичных методов
- Type hints для всех функций

## Troubleshooting

### "ModuleNotFoundError: No module named 'app'"
```bash
# Убедитесь что вы в директории сервиса
cd microservices/auth-service
python -m pytest test_auth.py
```

### Тесты падают с ошибкой БД
```bash
# Проверьте что используется in-memory БД
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
```

### CI/CD pipeline не запускается
- Проверьте наличие файла `.github/workflows/ci-cd.yml`
- Убедитесь что push в правильную ветку (main/develop)
- Проверьте синтаксис YAML файла

## Ресурсы

- [Pytest Documentation](https://docs.pytest.org/)
- [Flask Testing](https://flask.palletsprojects.com/en/latest/testing/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [GitHub Actions](https://docs.github.com/en/actions)
