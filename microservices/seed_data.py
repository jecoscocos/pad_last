"""
Скрипт для создания тестовых данных в микросервисах
"""
import requests
import time

BASE_URL = "http://localhost"
AUTH_URL = f"{BASE_URL}:5001"
PROPERTY_URL = f"{BASE_URL}:5002"
INQUIRY_URL = f"{BASE_URL}:5003"
PROJECT_URL = f"{BASE_URL}:5004"


def wait_for_services():
    """Ждем пока все сервисы станут доступны"""
    print("Ожидание запуска сервисов...")
    services = [
        (AUTH_URL, "auth-service"),
        (PROPERTY_URL, "property-service"),
        (INQUIRY_URL, "inquiry-service"),
        (PROJECT_URL, "project-service")
    ]
    
    for url, name in services:
        while True:
            try:
                response = requests.get(f"{url}/health", timeout=2)
                if response.status_code == 200:
                    print(f"✓ {name} готов")
                    break
            except:
                print(f"  Ожидание {name}...")
                time.sleep(2)


def create_users():
    """Создать тестовых пользователей"""
    print("\n=== Создание пользователей ===")
    
    users = [
        {"email": "admin@test.com", "password": "admin123", "role": "admin"},
        {"email": "agent@test.com", "password": "agent123", "role": "agent"},
        {"email": "user@test.com", "password": "user123", "role": "user"},
    ]
    
    tokens = {}
    
    for user in users:
        try:
            response = requests.post(f"{AUTH_URL}/register", json=user)
            if response.status_code == 201:
                data = response.json()
                tokens[user["role"]] = data["token"]
                print(f"✓ Создан {user['role']}: {user['email']}")
            else:
                print(f"✗ Ошибка создания {user['email']}: {response.json()}")
        except Exception as e:
            print(f"✗ Ошибка: {e}")
    
    return tokens


def create_properties(agent_token):
    """Создать тестовые объекты недвижимости"""
    print("\n=== Создание объектов недвижимости ===")
    
    properties = [
        {
            "title": "Современная квартира в центре Москвы",
            "description": "Прекрасная трехкомнатная квартира с видом на город",
            "city": "Москва",
            "address": "ул. Тверская, д. 15",
            "price_eur": 250000,
            "property_type": "apartment",
            "rooms": 3,
            "area_m2": 85.5,
            "is_for_sale": "true",
            "is_for_rent": "false"
        },
        {
            "title": "Загородный дом в Подмосковье",
            "description": "Уютный дом с участком",
            "city": "Московская область",
            "address": "пос. Солнечный, д. 42",
            "price_eur": 180000,
            "property_type": "house",
            "rooms": 5,
            "area_m2": 150.0,
            "is_for_sale": "true",
            "is_for_rent": "false"
        },
        {
            "title": "Офисное помещение",
            "description": "Готовое помещение под офис",
            "city": "Санкт-Петербург",
            "address": "Невский проспект, д. 100",
            "price_eur": 350000,
            "property_type": "commercial",
            "rooms": 0,
            "area_m2": 120.0,
            "is_for_sale": "false",
            "is_for_rent": "true"
        }
    ]
    
    property_ids = []
    headers = {"Authorization": f"Bearer {agent_token}"}
    
    for prop in properties:
        try:
            response = requests.post(
                f"{PROPERTY_URL}/properties",
                data=prop,
                headers=headers
            )
            if response.status_code == 201:
                data = response.json()
                property_ids.append(data["id"])
                print(f"✓ Создан объект: {prop['title']}")
            else:
                print(f"✗ Ошибка создания: {response.json()}")
        except Exception as e:
            print(f"✗ Ошибка: {e}")
    
    return property_ids


def create_inquiries(property_ids):
    """Создать тестовые заявки"""
    print("\n=== Создание заявок ===")
    
    inquiries = [
        {
            "property_id": property_ids[0] if property_ids else 1,
            "name": "Иван Петров",
            "email": "ivan@example.com",
            "phone": "+7 900 123-45-67",
            "message": "Интересует квартира, хочу посмотреть"
        },
        {
            "property_id": property_ids[1] if len(property_ids) > 1 else 1,
            "name": "Мария Сидорова",
            "email": "maria@example.com",
            "phone": "+7 901 234-56-78",
            "message": "Хочу купить дом"
        }
    ]
    
    for inq in inquiries:
        try:
            response = requests.post(f"{INQUIRY_URL}/inquiries", json=inq)
            if response.status_code == 201:
                print(f"✓ Создана заявка от {inq['name']}")
            else:
                print(f"✗ Ошибка: {response.json()}")
        except Exception as e:
            print(f"✗ Ошибка: {e}")


def create_projects(user_token):
    """Создать тестовые проекты"""
    print("\n=== Создание проектов ===")
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Создать проект
    project_data = {"name": "Ремонт квартиры"}
    try:
        response = requests.post(
            f"{PROJECT_URL}/projects",
            json=project_data,
            headers=headers
        )
        if response.status_code == 201:
            project = response.json()
            project_id = project["id"]
            print(f"✓ Создан проект: {project_data['name']}")
            
            # Создать задачи
            tasks = [
                {"title": "Купить обои", "status": "todo", "priority": 1},
                {"title": "Нанять рабочих", "status": "in_progress", "priority": 1},
                {"title": "Выбрать мебель", "status": "done", "priority": 2}
            ]
            
            for task in tasks:
                try:
                    response = requests.post(
                        f"{PROJECT_URL}/projects/{project_id}/tasks",
                        json=task,
                        headers=headers
                    )
                    if response.status_code == 201:
                        print(f"  ✓ Создана задача: {task['title']}")
                except Exception as e:
                    print(f"  ✗ Ошибка создания задачи: {e}")
    except Exception as e:
        print(f"✗ Ошибка: {e}")


def main():
    print("=" * 60)
    print("СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ")
    print("=" * 60)
    
    # Ждем запуска сервисов
    wait_for_services()
    
    # Создать пользователей
    tokens = create_users()
    
    if not tokens:
        print("\n✗ Не удалось создать пользователей")
        return
    
    # Создать объекты недвижимости
    property_ids = []
    if "agent" in tokens:
        property_ids = create_properties(tokens["agent"])
    
    # Создать заявки
    if property_ids:
        create_inquiries(property_ids)
    
    # Создать проекты
    if "user" in tokens:
        create_projects(tokens["user"])
    
    print("\n" + "=" * 60)
    print("ГОТОВО! Тестовые данные созданы")
    print("=" * 60)
    print("\nУчетные данные для входа:")
    print("  Админ:  admin@test.com / admin123")
    print("  Агент:  agent@test.com / agent123")
    print("  Юзер:   user@test.com / user123")
    print("\nОткройте http://localhost:5000 для доступа к приложению")


if __name__ == "__main__":
    main()
