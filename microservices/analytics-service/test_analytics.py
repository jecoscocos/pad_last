import unittest
import json
from app import app, db, Event


class AnalyticsServiceTestCase(unittest.TestCase):
    """Unit tests for Analytics Service"""
    
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
    
    def test_track_event(self):
        """Test tracking an analytics event"""
        response = self.client.post('/events', json={
            'event_type': 'page_view',
            'user_id': 1,
            'metadata': '/properties'
        })
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['event_type'], 'page_view')
        self.assertEqual(data['user_id'], 1)
    
    def test_get_events(self):
        """Test getting analytics events"""
        # Create some events
        with app.app_context():
            event1 = Event(event_type='page_view', user_id=1)
            event2 = Event(event_type='click', user_id=2)
            db.session.add_all([event1, event2])
            db.session.commit()
        
        response = self.client.get('/events')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
    
    def test_get_stats(self):
        """Test getting analytics statistics"""
        # Create test events
        with app.app_context():
            events = [
                Event(event_type='page_view', user_id=1),
                Event(event_type='page_view', user_id=2),
                Event(event_type='page_view', user_id=1),  # Same user
                Event(event_type='click', user_id=3),
            ]
            db.session.add_all(events)
            db.session.commit()
        
        response = self.client.get('/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(data['total_events'], 4)
        self.assertEqual(data['total_views'], 3)
        self.assertEqual(data['unique_users'], 3)
        self.assertIn('events_by_type', data)
    
    def test_filter_events_by_type(self):
        """Test filtering events by type"""
        with app.app_context():
            event1 = Event(event_type='page_view', user_id=1)
            event2 = Event(event_type='click', user_id=2)
            event3 = Event(event_type='page_view', user_id=3)
            db.session.add_all([event1, event2, event3])
            db.session.commit()
        
        response = self.client.get('/events?event_type=page_view')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
        for event in data:
            self.assertEqual(event['event_type'], 'page_view')
    
    def test_event_model_to_dict(self):
        """Test Event model to_dict method"""
        with app.app_context():
            event = Event(
                event_type='search',
                resource_id=123,
                user_id=1,
                event_metadata='city=Chisinau'
            )
            db.session.add(event)
            db.session.commit()
            
            event_dict = event.to_dict()
            self.assertIsInstance(event_dict, dict)
            self.assertEqual(event_dict['event_type'], 'search')
            self.assertEqual(event_dict['user_id'], 1)
            self.assertIn('id', event_dict)
            self.assertIn('created_at', event_dict)


if __name__ == '__main__':
    unittest.main()
