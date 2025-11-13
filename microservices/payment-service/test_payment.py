import unittest
import json
from app import app, db, Transaction

class TestPaymentService(unittest.TestCase):
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
    
    def test_health_check(self):
        """Тест health endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
    
    def test_get_transactions(self):
        """Тест получения списка транзакций"""
        response = self.client.get('/transactions')
        self.assertIn(response.status_code, [200, 401])

if __name__ == '__main__':
    unittest.main()
