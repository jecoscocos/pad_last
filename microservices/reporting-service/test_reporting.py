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
    
    def test_get_sales_report(self):
        """Тест получения отчета по продажам"""
        response = self.client.get('/reports/sales')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('total_sales', data)
    
    def test_get_user_activity_report(self):
        """Тест отчета по активности пользователей"""
        response = self.client.get('/reports/user-activity')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('total_users', data)
    
    def test_get_property_statistics(self):
        """Тест статистики по недвижимости"""
        response = self.client.get('/reports/property-stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, dict)
    
    def test_generate_custom_report(self):
        """Тест генерации кастомного отчета"""
        params = {
            'start_date': '2025-01-01',
            'end_date': '2025-12-31',
            'report_type': 'inquiries'
        }
        response = self.client.get('/reports/custom', query_string=params)
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
