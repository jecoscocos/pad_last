import unittest
from app import app

class TestAPIGateway(unittest.TestCase):
    def setUp(self):
        """Подготовка перед каждым тестом"""
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def test_health_check(self):
        """Тест health endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
    
    def test_index_page(self):
        """Тест главной страницы"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_login_page(self):
        """Тест страницы входа"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
    
    def test_register_page(self):
        """Тест страницы регистрации"""
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
    
    def test_properties_page(self):
        """Тест страницы недвижимости"""
        response = self.client.get('/properties')
        # Может быть 200 или 302 (redirect)
        self.assertIn(response.status_code, [200, 302])
    
    def test_projects_page(self):
        """Тест страницы проектов"""
        response = self.client.get('/projects')
        self.assertIn(response.status_code, [200, 302])
    
    def test_analytics_page(self):
        """Тест страницы аналитики"""
        response = self.client.get('/analytics')
        self.assertIn(response.status_code, [200, 302])
    
    def test_reports_page(self):
        """Тест страницы отчетов"""
        response = self.client.get('/reports')
        self.assertIn(response.status_code, [200, 302])

if __name__ == '__main__':
    unittest.main()
