import unittest
import json
from app import app, db, Notification


class NotificationServiceTestCase(unittest.TestCase):
    """Unit tests for Notification Service"""
    
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
    
    def test_create_notification(self):
        """Test creating a notification"""
        response = self.client.post('/notifications', json={
            'recipient': 'test@example.com',
            'channel': 'email',
            'message': 'Test notification message'
        })
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['recipient'], 'test@example.com')
        self.assertEqual(data['channel'], 'email')
        self.assertEqual(data['message'], 'Test notification message')
    
    def test_create_notification_missing_fields(self):
        """Test creating notification without required fields"""
        response = self.client.post('/notifications', json={
            'recipient': 'test@example.com'
            # Missing message
        })
        self.assertEqual(response.status_code, 400)
    
    def test_notification_channels(self):
        """Test different notification channels"""
        channels = ['email', 'sms', 'push']
        
        for channel in channels:
            response = self.client.post('/notifications', json={
                'recipient': 'test@example.com',
                'channel': channel,
                'message': f'Test {channel} notification'
            })
            self.assertEqual(response.status_code, 201)
            data = json.loads(response.data)
            self.assertEqual(data['channel'], channel)
    
    def test_notification_model_to_dict(self):
        """Test Notification model to_dict method"""
        with app.app_context():
            notif = Notification(
                recipient='test@example.com',
                channel='push',
                message='Test message'
            )
            db.session.add(notif)
            db.session.commit()
            
            notif_dict = notif.to_dict()
            self.assertIsInstance(notif_dict, dict)
            self.assertEqual(notif_dict['recipient'], 'test@example.com')
            self.assertEqual(notif_dict['channel'], 'push')
            self.assertIn('id', notif_dict)
            self.assertIn('created_at', notif_dict)


if __name__ == '__main__':
    unittest.main()
