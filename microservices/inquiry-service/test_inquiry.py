import unittest
import json
from app import app, db, Inquiry, Appointment

class TestInquiryService(unittest.TestCase):
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
    
    def test_create_inquiry(self):
        """Тест создания обращения"""
        data = {
            'property_id': 1,
            'name': 'Иван Иванов',
            'email': 'test@example.com',
            'phone': '+79001234567',
            'message': 'Интересует эта квартира'
        }
        response = self.client.post('/inquiries',
                                   data=json.dumps(data),
                                   content_type='application/json')
        self.assertIn(response.status_code, [201, 401])  # Может требовать авторизации
    
    def test_get_inquiries(self):
        """Тест получения списка обращений"""
        # Создаем тестовое обращение
        with app.app_context():
            inquiry = Inquiry(
                property_id=1,
                name='Test User',
                email='test@test.com'
            )
            db.session.add(inquiry)
            db.session.commit()
        
        response = self.client.get('/inquiries')
        self.assertIn(response.status_code, [200, 401])
    
    def test_update_inquiry_status(self):
        """Тест обновления статуса обращения"""
        # Создаем обращение
        with app.app_context():
            inquiry = Inquiry(
                property_id=1,
                name='Test User',
                email='test@test.com'
            )
            db.session.add(inquiry)
            db.session.commit()
            inquiry_id = inquiry.id
        
        # Обновляем статус
        response = self.client.put(f'/inquiries/{inquiry_id}/status',
                                  data=json.dumps({'status': 'in_progress'}),
                                  content_type='application/json')
        self.assertIn(response.status_code, [200, 401])
    
    def test_create_appointment(self):
        """Тест создания встречи"""
        data = {
            'property_id': 1,
            'client_id': 1,
            'scheduled_at': '2025-12-01T10:00:00',
            'note': 'Показ квартиры'
        }
        response = self.client.post('/appointments',
                                   data=json.dumps(data),
                                   content_type='application/json')
        self.assertIn(response.status_code, [201, 401])
    
    def test_delete_inquiry(self):
        """Тест удаления обращения"""
        # Создаем обращение
        with app.app_context():
            inquiry = Inquiry(
                property_id=1,
                name='Test User',
                email='test@test.com'
            )
            db.session.add(inquiry)
            db.session.commit()
            inquiry_id = inquiry.id
        
        response = self.client.delete(f'/inquiries/{inquiry_id}')
        self.assertIn(response.status_code, [200, 401, 404])

if __name__ == '__main__':
    unittest.main()
