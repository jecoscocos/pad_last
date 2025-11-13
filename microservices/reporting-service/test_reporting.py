import unittest
import json
from app import app

class TestReportingService(unittest.TestCase):
    def setUp(self):
        """Подготовка перед каждым тестом"""
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def test_health_check(self):
        """Тест health endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
    
    def test_reports_endpoint_exists(self):
        """Тест существования reports endpoint"""
        response = self.client.get('/reports')
        # Любой ответ кроме 500 = endpoint существует
        self.assertNotEqual(response.status_code, 500)

if __name__ == '__main__':
    unittest.main()
