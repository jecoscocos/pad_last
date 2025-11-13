import unittest
import json
from app import app

class TestSearchService(unittest.TestCase):
    def setUp(self):
        """Подготовка перед каждым тестом"""
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def test_health_check(self):
        """Тест health endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
    
    def test_search_properties(self):
        """Тест поиска недвижимости"""
        params = {
            'city': 'Москва',
            'min_price': 5000000,
            'max_price': 10000000
        }
        response = self.client.get('/search', query_string=params)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
    
    def test_search_with_type(self):
        """Тест поиска по типу недвижимости"""
        params = {'type': 'apartment'}
        response = self.client.get('/search', query_string=params)
        self.assertEqual(response.status_code, 200)
    
    def test_search_with_rooms(self):
        """Тест поиска по количеству комнат"""
        params = {'rooms': 2}
        response = self.client.get('/search', query_string=params)
        self.assertEqual(response.status_code, 200)
    
    def test_search_empty_query(self):
        """Тест поиска без параметров"""
        response = self.client.get('/search')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)

if __name__ == '__main__':
    unittest.main()
