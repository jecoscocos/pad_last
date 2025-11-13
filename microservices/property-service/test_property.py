import unittest
import json
from app import app, db, Property, Photo


class PropertyServiceTestCase(unittest.TestCase):
    """Unit tests for Property Service"""
    
    def setUp(self):
        """Set up test client and database"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after tests"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_health_check(self):
        """Test /health endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'property-service')
    
    def test_get_properties_empty(self):
        """Test getting properties when none exist"""
        response = self.client.get('/properties')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 0)
    
    def test_get_properties_with_data(self):
        """Test getting properties with existing data"""
        with app.app_context():
            prop1 = Property(
                title="Квартира в центре",
                city="Кишинев",
                address="ул. Ленина, 10",
                price_eur=50000,
                property_type="apartment",
                rooms=2,
                area_m2=60
            )
            prop2 = Property(
                title="Дом на окраине",
                city="Бельцы",
                address="ул. Пушкина, 5",
                price_eur=80000,
                property_type="house",
                rooms=4,
                area_m2=120
            )
            db.session.add_all([prop1, prop2])
            db.session.commit()
        
        response = self.client.get('/properties')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
    
    def test_get_property_by_id(self):
        """Test getting single property by ID"""
        with app.app_context():
            prop = Property(
                title="Test Property",
                city="Test City",
                address="Test Address",
                price_eur=100000,
                property_type="apartment"
            )
            db.session.add(prop)
            db.session.commit()
            prop_id = prop.id
        
        response = self.client.get(f'/properties/{prop_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['title'], "Test Property")
        self.assertEqual(data['city'], "Test City")
    
    def test_get_property_not_found(self):
        """Test getting non-existent property"""
        response = self.client.get('/properties/9999')
        self.assertEqual(response.status_code, 404)
    
    def test_filter_properties_by_city(self):
        """Test filtering properties by city"""
        with app.app_context():
            prop1 = Property(title="P1", city="Кишинев", address="A1", price_eur=1000, property_type="apartment")
            prop2 = Property(title="P2", city="Бельцы", address="A2", price_eur=2000, property_type="house")
            db.session.add_all([prop1, prop2])
            db.session.commit()
        
        response = self.client.get('/properties?city=Кишинев')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['city'], "Кишинев")
    
    def test_filter_properties_by_type(self):
        """Test filtering properties by type"""
        with app.app_context():
            prop1 = Property(title="P1", city="C1", address="A1", price_eur=1000, property_type="apartment")
            prop2 = Property(title="P2", city="C2", address="A2", price_eur=2000, property_type="house")
            db.session.add_all([prop1, prop2])
            db.session.commit()
        
        response = self.client.get('/properties?property_type=house')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['property_type'], "house")
    
    def test_filter_properties_by_price(self):
        """Test filtering properties by price range"""
        with app.app_context():
            prop1 = Property(title="P1", city="C1", address="A1", price_eur=30000, property_type="apartment")
            prop2 = Property(title="P2", city="C2", address="A2", price_eur=60000, property_type="apartment")
            prop3 = Property(title="P3", city="C3", address="A3", price_eur=90000, property_type="apartment")
            db.session.add_all([prop1, prop2, prop3])
            db.session.commit()
        
        response = self.client.get('/properties?min_price=40000&max_price=70000')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['price_eur'], 60000)
    
    def test_property_model_to_dict(self):
        """Test Property model to_dict method"""
        with app.app_context():
            prop = Property(
                title="Test",
                city="City",
                address="Address",
                price_eur=50000,
                property_type="apartment",
                rooms=2,
                area_m2=60,
                is_for_sale=True,
                is_for_rent=False
            )
            db.session.add(prop)
            db.session.commit()
            
            prop_dict = prop.to_dict()
            self.assertIsInstance(prop_dict, dict)
            self.assertEqual(prop_dict['title'], "Test")
            self.assertEqual(prop_dict['price_eur'], 50000)
            self.assertIn('id', prop_dict)
            self.assertIn('created_at', prop_dict)


if __name__ == '__main__':
    unittest.main()
