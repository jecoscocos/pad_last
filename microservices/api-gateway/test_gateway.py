import unittest
from app import app

class TestAPIGateway(unittest.TestCase):
    def setUp(self):
        """Подготовка перед каждым тестом"""
        app.config['TESTING'] = True
        self.client = app.test_client()
    
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
    
    def test_analytics_page(self):
        """Тест страницы аналитики"""
        response = self.client.get('/analytics')
        # Может требовать авторизации - 200 или 302
        self.assertIn(response.status_code, [200, 302])
    
    def test_reports_page(self):
        """Тест страницы отчетов"""
        response = self.client.get('/reports')
        # Может требовать авторизации
        self.assertIn(response.status_code, [200, 302])
    
    def test_404_page(self):
        """Тест несуществующей страницы"""
        response = self.client.get('/nonexistent-page')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
