import unittest
import json
from app import app, db, Project

class TestProjectService(unittest.TestCase):
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
    
    def test_create_project(self):
        """Тест создания проекта"""
        data = {
            'name': 'Новый ЖК Заречный',
            'description': 'Современный жилой комплекс',
            'location': 'г. Москва, ул. Заречная',
            'developer': 'ООО СтройИнвест',
            'status': 'in_progress'
        }
        response = self.client.post('/projects',
                                   data=json.dumps(data),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertIn('id', response_data)
        self.assertEqual(response_data['name'], 'Новый ЖК Заречный')
    
    def test_get_projects(self):
        """Тест получения списка проектов"""
        # Создаем тестовый проект
        with app.app_context():
            project = Project(
                name='Test Project',
                description='Test',
                location='Moscow',
                developer='Test Dev'
            )
            db.session.add(project)
            db.session.commit()
        
        response = self.client.get('/projects')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
    
    def test_get_project_by_id(self):
        """Тест получения проекта по ID"""
        # Создаем проект
        with app.app_context():
            project = Project(
                name='Test Project',
                description='Test',
                location='Moscow',
                developer='Test Dev'
            )
            db.session.add(project)
            db.session.commit()
            project_id = project.id
        
        response = self.client.get(f'/projects/{project_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['name'], 'Test Project')
    
    def test_update_project(self):
        """Тест обновления проекта"""
        # Создаем проект
        with app.app_context():
            project = Project(
                name='Old Name',
                description='Test',
                location='Moscow',
                developer='Test Dev'
            )
            db.session.add(project)
            db.session.commit()
            project_id = project.id
        
        # Обновляем
        update_data = {'name': 'New Name'}
        response = self.client.put(f'/projects/{project_id}',
                                  data=json.dumps(update_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Проверяем
        response = self.client.get(f'/projects/{project_id}')
        data = json.loads(response.data)
        self.assertEqual(data['name'], 'New Name')
    
    def test_project_serialization(self):
        """Тест сериализации модели Project"""
        with app.app_context():
            project = Project(
                name='Test',
                description='Desc',
                location='Moscow',
                developer='Dev'
            )
            db.session.add(project)
            db.session.commit()
            
            data = project.to_dict()
            self.assertIn('id', data)
            self.assertIn('name', data)
            self.assertEqual(data['name'], 'Test')

if __name__ == '__main__':
    unittest.main()
