"""
Script to add test properties to the Property Service
"""
import requests

# Configuration
AUTH_SERVICE_URL = "http://localhost:5001"
PROPERTY_SERVICE_URL = "http://localhost:5002"

AGENT_EMAIL = "agent@test.com"
AGENT_PASSWORD = "123456"

# Login as agent
print("Logging in as agent...")
response = requests.post(
    f"{AUTH_SERVICE_URL}/login",
    json={"email": AGENT_EMAIL, "password": AGENT_PASSWORD}
)

if response.status_code != 200:
    print(f"Failed to login: {response.text}")
    exit(1)

token = response.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

print(f"Logged in successfully. Token: {token[:20]}...")

# Test properties
properties = [
    {
        "title": "Квартира в центре Москвы",
        "description": "Уютная 2-комнатная квартира с евроремонтом в самом центре столицы",
        "city": "Москва",
        "address": "Москва, ул. Тверская, д. 10, кв. 25",
        "price_eur": "250000",
        "property_type": "apartment",
        "rooms": "2",
        "area_m2": "65.5",
        "is_for_sale": "true",
        "is_for_rent": "false"
    },
    {
        "title": "Загородный дом в Подмосковье",
        "description": "Просторный дом с участком 15 соток, рядом с лесом",
        "city": "Московская область",
        "address": "Одинцовский район, д. Жуковка",
        "price_eur": "450000",
        "property_type": "house",
        "rooms": "5",
        "area_m2": "180",
        "is_for_sale": "true",
        "is_for_rent": "false"
    },
    {
        "title": "Офис в бизнес-центре",
        "description": "Современное офисное помещение класса А",
        "city": "Москва",
        "address": "Москва, Пресненская наб., д. 12",
        "price_eur": "3500",
        "property_type": "commercial",
        "rooms": "0",
        "area_m2": "85",
        "is_for_sale": "false",
        "is_for_rent": "true"
    },
    {
        "title": "Студия у метро",
        "description": "Компактная студия в новостройке, 3 минуты пешком от метро",
        "city": "Санкт-Петербург",
        "address": "Санкт-Петербург, пр. Просвещения, д. 87",
        "price_eur": "120000",
        "property_type": "apartment",
        "rooms": "1",
        "area_m2": "28",
        "is_for_sale": "true",
        "is_for_rent": "false"
    },
    {
        "title": "Земельный участок под строительство",
        "description": "Участок 20 соток с коммуникациями и разрешением на строительство",
        "city": "Краснодарский край",
        "address": "Краснодар, мкр. Прикубанский",
        "price_eur": "80000",
        "property_type": "land",
        "rooms": "0",
        "area_m2": "2000",
        "is_for_sale": "true",
        "is_for_rent": "false"
    }
]

# Create properties
print(f"\nCreating {len(properties)} test properties...")

for i, prop_data in enumerate(properties, 1):
    print(f"\n{i}. Creating: {prop_data['title']}")
    response = requests.post(
        f"{PROPERTY_SERVICE_URL}/properties",
        headers=headers,
        data=prop_data
    )
    
    if response.status_code == 201:
        prop = response.json()
        print(f"   ✓ Created property ID: {prop['id']}")
        print(f"   Price: €{prop['price_eur']:,.0f}")
        print(f"   Area: {prop['area_m2']} m²")
    else:
        print(f"   ✗ Failed: {response.text}")

print("\n" + "="*60)
print("Done! Check the property catalog at http://localhost:5000/properties")
print("="*60)
