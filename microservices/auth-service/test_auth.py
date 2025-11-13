import unittest
import json
from app import app, db, User, hash_password


class AuthServiceTestCase(unittest.TestCase):
    """Unit tests for Auth Service"""
    
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
        self.assertEqual(data['service'], 'auth-service')
    
    def test_register_user_success(self):
        """Test successful user registration"""
        response = self.client.post('/register', json={
            'email': 'test@example.com',
            'password': 'testpass123',
            'role': 'user'
        })
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('user', data)
        self.assertIn('token', data)
        self.assertEqual(data['user']['email'], 'test@example.com')
        self.assertEqual(data['user']['role'], 'user')
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        # Register first user
        self.client.post('/register', json={
            'email': 'test@example.com',
            'password': 'pass1'
        })
        
        # Try to register again with same email
        response = self.client.post('/register', json={
            'email': 'test@example.com',
            'password': 'pass2'
        })
        self.assertEqual(response.status_code, 409)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_register_missing_fields(self):
        """Test registration with missing fields"""
        response = self.client.post('/register', json={
            'email': 'test@example.com'
            # Missing password
        })
        self.assertEqual(response.status_code, 400)
    
    def test_login_success(self):
        """Test successful login"""
        # Register user first
        self.client.post('/register', json={
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        # Login
        response = self.client.post('/login', json={
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('user', data)
        self.assertIn('token', data)
    
    def test_login_wrong_password(self):
        """Test login with wrong password"""
        # Register user
        self.client.post('/register', json={
            'email': 'test@example.com',
            'password': 'correctpass'
        })
        
        # Try to login with wrong password
        response = self.client.post('/login', json={
            'email': 'test@example.com',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 401)
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent user"""
        response = self.client.post('/login', json={
            'email': 'nonexistent@example.com',
            'password': 'anypass'
        })
        self.assertEqual(response.status_code, 401)
    
    def test_verify_token_valid(self):
        """Test token verification with valid token"""
        # Register and get token
        reg_response = self.client.post('/register', json={
            'email': 'test@example.com',
            'password': 'testpass'
        })
        token = json.loads(reg_response.data)['token']
        
        # Verify token
        response = self.client.post('/verify', json={'token': token})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['email'], 'test@example.com')
    
    def test_verify_token_invalid(self):
        """Test token verification with invalid token"""
        response = self.client.post('/verify', json={'token': 'invalid_token'})
        self.assertEqual(response.status_code, 401)
    
    def test_verify_token_missing(self):
        """Test token verification without token"""
        response = self.client.post('/verify', json={})
        self.assertEqual(response.status_code, 400)
    
    def test_get_users(self):
        """Test getting all users"""
        # Create some users
        with app.app_context():
            user1 = User(email='user1@test.com', password_hash=hash_password('pass1'))
            user2 = User(email='user2@test.com', password_hash=hash_password('pass2'))
            db.session.add_all([user1, user2])
            db.session.commit()
        
        response = self.client.get('/users')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "test_password_123"
        hashed = hash_password(password)
        self.assertIsInstance(hashed, str)
        self.assertNotEqual(hashed, password)
        self.assertEqual(hash_password(password), hashed)  # Same input = same hash


if __name__ == '__main__':
    unittest.main()
