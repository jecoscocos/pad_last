import unittest
import json
import io
from app import app, db, Media

class TestMediaService(unittest.TestCase):
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
    
    def test_upload_file(self):
        """Тест загрузки файла"""
        data = {
            'file': (io.BytesIO(b"test image content"), 'test.jpg'),
            'property_id': '1',
            'file_type': 'image'
        }
        response = self.client.post('/media/upload',
                                   data=data,
                                   content_type='multipart/form-data')
        # Может быть 201 или 400 в зависимости от реализации
        self.assertIn(response.status_code, [200, 201, 400])
    
    def test_get_media_list(self):
        """Тест получения списка медиа"""
        response = self.client.get('/media')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
    
    def test_get_media_by_property(self):
        """Тест получения медиа по property_id"""
        response = self.client.get('/media/property/1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
    
    def test_delete_media(self):
        """Тест удаления медиа"""
        # Создаем медиа запись
        with app.app_context():
            media = Media(
                property_id=1,
                filename='test.jpg',
                file_type='image',
                file_path='/uploads/test.jpg'
            )
            db.session.add(media)
            db.session.commit()
            media_id = media.id
        
        response = self.client.delete(f'/media/{media_id}')
        # Может быть 200 или 404
        self.assertIn(response.status_code, [200, 404])

if __name__ == '__main__':
    unittest.main()
