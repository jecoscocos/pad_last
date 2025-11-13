import unittest
import json
from app import app, db, Payment

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
    
    def test_create_payment(self):
        """Тест создания платежа"""
        data = {
            'property_id': 1,
            'user_id': 1,
            'amount': 50000.00,
            'payment_type': 'deposit',
            'payment_method': 'card'
        }
        response = self.client.post('/payments',
                                   data=json.dumps(data),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertIn('id', response_data)
        self.assertEqual(response_data['amount'], 50000.00)
    
    def test_get_payments(self):
        """Тест получения списка платежей"""
        # Создаем тестовый платеж
        with app.app_context():
            payment = Payment(
                property_id=1,
                user_id=1,
                amount=10000.00,
                payment_type='deposit'
            )
            db.session.add(payment)
            db.session.commit()
        
        response = self.client.get('/payments')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
    
    def test_get_payment_by_id(self):
        """Тест получения платежа по ID"""
        with app.app_context():
            payment = Payment(
                property_id=1,
                user_id=1,
                amount=25000.00,
                payment_type='deposit'
            )
            db.session.add(payment)
            db.session.commit()
            payment_id = payment.id
        
        response = self.client.get(f'/payments/{payment_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['amount'], 25000.00)
    
    def test_update_payment_status(self):
        """Тест обновления статуса платежа"""
        with app.app_context():
            payment = Payment(
                property_id=1,
                user_id=1,
                amount=15000.00,
                payment_type='deposit'
            )
            db.session.add(payment)
            db.session.commit()
            payment_id = payment.id
        
        response = self.client.put(f'/payments/{payment_id}/status',
                                  data=json.dumps({'status': 'completed'}),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
