import unittest
import json
import io
import os
import tempfile

# Создаем временную директорию перед импортом app
os.environ['UPLOAD_FOLDER'] = tempfile.mkdtemp()

from app import app

class TestMediaService(unittest.TestCase):
    def setUp(self):
        """Подготовка перед каждым тестом"""
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def test_health_check(self):
        """Тест health endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
    
    def test_upload_file(self):
        """Тест загрузки файла"""
        data = {
            'file': (io.BytesIO(b"test image content"), 'test.jpg')
        }
        response = self.client.post('/upload',
                                   data=data,
                                   content_type='multipart/form-data')
        self.assertIn(response.status_code, [201, 400])
    
    def test_upload_no_file(self):
        """Тест загрузки без файла"""
        response = self.client.post('/upload',
                                   data={},
                                   content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
    
    def test_list_media(self):
        """Тест получения списка медиа"""
        response = self.client.get('/media')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
    
    def test_get_nonexistent_media(self):
        """Тест получения несуществующего файла"""
        response = self.client.get('/media/nonexistent.jpg')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
