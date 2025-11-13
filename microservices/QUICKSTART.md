# Quick Start Guide

## Быстрый запуск

### 1. Запустить все сервисы:
```bash
cd microservices
docker-compose up --build
```

### 2. Открыть приложение:
Перейти на http://localhost:5000

### 3. Создать тестового агента:

#### Вариант A - Через API:
```bash
curl -X POST http://localhost:5001/register ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"agent@test.com\",\"password\":\"123456\",\"role\":\"agent\"}"
```

#### Вариант B - Через UI:
1. Зарегистрироваться на http://localhost:5000/register
2. Вручную изменить роль в базе данных auth.db

### 4. Войти как агент:
- Email: agent@test.com
- Password: 123456

### 5. Создать объект недвижимости:
Перейти на http://localhost:5000/properties/new

---

## Остановка сервисов

```bash
# Остановить без удаления данных
docker-compose down

# Остановить с удалением данных
docker-compose down -v
```

---

## Проверка работоспособности

### Все сервисы здоровы:
```bash
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health
curl http://localhost:5004/health
```

### Просмотр логов:
```bash
# Все сервисы
docker-compose logs

# Конкретный сервис
docker-compose logs auth-service
docker-compose logs property-service
```

---

## Основные эндпоинты

### API Gateway (Frontend)
- http://localhost:5000 - Главная страница
- http://localhost:5000/register - Регистрация
- http://localhost:5000/login - Вход
- http://localhost:5000/properties/new - Добавить объект (agent)

### Auth Service API
- POST http://localhost:5001/register - Регистрация
- POST http://localhost:5001/login - Вход
- POST http://localhost:5001/verify - Проверка токена

### Property Service API
- GET http://localhost:5002/properties - Список объектов
- POST http://localhost:5002/properties - Создать объект (требует токен)

### Inquiry Service API
- POST http://localhost:5003/inquiries - Создать заявку
- GET http://localhost:5003/inquiries - Список заявок (требует токен)

### Project Service API
- POST http://localhost:5004/projects - Создать проект (требует токен)
- GET http://localhost:5004/projects - Список проектов (требует токен)

---

## Troubleshooting

### Порты заняты:
Измените порты в docker-compose.yml:
```yaml
ports:
  - "8000:5000"  # вместо 5000:5000
```

### Сервис не запускается:
```bash
docker-compose logs service-name
docker-compose restart service-name
```

### Пересобрать конкретный сервис:
```bash
docker-compose up --build --force-recreate service-name
```
