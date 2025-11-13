# API Documentation

## Auth Service (Port 5001)

### POST /register
Регистрация нового пользователя

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "role": "user"  // optional: user|agent|admin (default: user)
}
```

**Response (201):**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "user",
    "created_at": "2025-10-20T12:00:00"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### POST /login
Вход в систему

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "user",
    "created_at": "2025-10-20T12:00:00"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### POST /verify
Проверка JWT токена

**Request:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "user_id": 1,
  "email": "user@example.com",
  "role": "user",
  "exp": 1729598400
}
```

---

## Property Service (Port 5002)

### GET /properties
Получить список объектов недвижимости

**Query Parameters:**
- `city` - фильтр по городу
- `property_type` - тип объекта (apartment|house|land|commercial)
- `min_price` - минимальная цена
- `max_price` - максимальная цена

**Response (200):**
```json
[
  {
    "id": 1,
    "title": "Квартира в центре",
    "description": "Прекрасная квартира",
    "city": "Москва",
    "address": "ул. Пушкина, д. 10",
    "price_eur": 150000,
    "property_type": "apartment",
    "rooms": 3,
    "area_m2": 75.0,
    "is_for_sale": true,
    "is_for_rent": false,
    "created_at": "2025-10-20T12:00:00",
    "photos": [
      {
        "id": 1,
        "property_id": 1,
        "file_path": "uuid_filename.jpg",
        "created_at": "2025-10-20T12:00:00"
      }
    ]
  }
]
```

---

### POST /properties
Создать объект недвижимости (требует токен агента)

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Form Data:**
- `title` - название
- `description` - описание (optional)
- `city` - город
- `address` - адрес
- `price_eur` - цена в евро
- `property_type` - тип (apartment|house|land|commercial)
- `rooms` - количество комнат (optional)
- `area_m2` - площадь (optional)
- `is_for_sale` - продажа (true/false)
- `is_for_rent` - аренда (true/false)
- `photos` - файлы фотографий (multiple)

**Response (201):**
```json
{
  "id": 1,
  "title": "Квартира в центре",
  ...
}
```

---

### PUT /properties/{id}
Обновить объект недвижимости (требует токен агента)

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Request:**
```json
{
  "title": "Новое название",
  "price_eur": 160000
}
```

---

### DELETE /properties/{id}
Удалить объект недвижимости (требует токен агента)

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response (200):**
```json
{
  "message": "Property deleted"
}
```

---

## Inquiry Service (Port 5003)

### POST /inquiries
Создать заявку (публичный эндпоинт)

**Request:**
```json
{
  "property_id": 1,
  "name": "Иван Иванов",
  "email": "ivan@example.com",
  "phone": "+7 900 123-45-67",
  "message": "Хочу посмотреть квартиру"
}
```

**Response (201):**
```json
{
  "id": 1,
  "property_id": 1,
  "client_id": 1,
  "name": "Иван Иванов",
  "email": "ivan@example.com",
  "phone": "+7 900 123-45-67",
  "message": "Хочу посмотреть квартиру",
  "status": "new",
  "created_at": "2025-10-20T12:00:00"
}
```

---

### GET /inquiries
Получить заявки (требует токен)

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response (200):**
- Агент видит все заявки
- Пользователь видит только свои заявки

---

### PUT /inquiries/{id}/status
Изменить статус заявки (требует токен агента)

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Request:**
```json
{
  "status": "in_progress"  // new|in_progress|done|rejected
}
```

---

### POST /appointments
Создать встречу (требует токен)

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Request:**
```json
{
  "property_id": 1,
  "client_name": "Иван Иванов",
  "client_email": "ivan@example.com",
  "client_phone": "+7 900 123-45-67",
  "scheduled_at": "2025-10-25T14:00:00",
  "note": "Показ квартиры"
}
```

---

## Project Service (Port 5004)

### POST /projects
Создать проект (требует токен)

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Request:**
```json
{
  "name": "Мой проект"
}
```

**Response (201):**
```json
{
  "id": 1,
  "name": "Мой проект",
  "owner_id": 1,
  "created_at": "2025-10-20T12:00:00",
  "tasks": [],
  "members": []
}
```

---

### GET /projects
Получить список проектов пользователя (требует токен)

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

---

### POST /projects/{id}/tasks
Создать задачу в проекте (требует токен)

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Request:**
```json
{
  "title": "Новая задача",
  "description": "Описание задачи",
  "status": "todo",
  "priority": 1,
  "due_date": "2025-10-30T23:59:59"
}
```

---

### POST /tasks/{id}/toggle
Переключить статус выполнения задачи (требует токен)

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

---

### POST /tasks/{id}/comments
Добавить комментарий к задаче (требует токен)

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Request:**
```json
{
  "body": "Текст комментария"
}
```

---

## Коды ошибок

- `200` - OK
- `201` - Created
- `400` - Bad Request (неверные данные)
- `401` - Unauthorized (нет токена или токен невалиден)
- `403` - Forbidden (нет прав)
- `404` - Not Found
- `409` - Conflict (например, пользователь уже существует)
- `500` - Internal Server Error
