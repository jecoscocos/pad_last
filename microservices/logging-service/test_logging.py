import unittest
import json
from app import app, db, Log

class TestLoggingService(unittest.TestCase):
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
    
    def test_create_log(self):
        """Тест создания лога"""
        data = {
            'service_name': 'auth-service',
            'level': 'INFO',
            'message': 'User logged in',
            'user_id': 1
        }
        response = self.client.post('/logs',
                                   data=json.dumps(data),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertIn('id', response_data)
    
    def test_get_logs(self):
        """Тест получения логов"""
        # Создаем тестовый лог
        with app.app_context():
            log = Log(
                service_name='test-service',
                level='INFO',
                message='Test message'
            )
            db.session.add(log)
            db.session.commit()
        
        response = self.client.get('/logs')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
    
    def test_get_logs_by_service(self):
        """Тест получения логов по сервису"""
        with app.app_context():
            log = Log(
                service_name='auth-service',
                level='INFO',
                message='Test'
            )
            db.session.add(log)
            db.session.commit()
        
        response = self.client.get('/logs/service/auth-service')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
    
    def test_get_logs_by_level(self):
        """Тест получения логов по уровню"""
        with app.app_context():
            log = Log(
                service_name='test-service',
                level='ERROR',
                message='Error message'
            )
            db.session.add(log)
            db.session.commit()
        
        response = self.client.get('/logs/level/ERROR')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
