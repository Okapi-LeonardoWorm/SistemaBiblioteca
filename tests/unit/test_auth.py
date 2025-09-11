from tests.unit.base import BaseTestCase
from flask import url_for
from app.models import User
from app import db, bcrypt

class TestAuth(BaseTestCase):

    def setUp(self):
        super().setUp()
        # Create a user with a hashed password for login tests
        hashed_password = bcrypt.generate_password_hash('testpassword').decode('utf-8')
        user = User(
            username='testuser', 
            password=hashed_password, 
            userType='student', 
            birthDate='2000-01-01',
            createdBy=1,  # Assuming a default creator
            updatedBy=1
        )
        db.session.add(user)
        db.session.commit()

    def test_login_page_loads(self):
        """Test that the login page loads correctly."""
        response = self.client.get(url_for('main.login'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Login', response.get_data(as_text=True))

    def test_successful_login(self):
        """Test that a user can log in successfully."""
        response = self.client.post(url_for('main.login'), data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Olá, testuser!', response.get_data(as_text=True))

    def test_failed_login_wrong_password(self):
        """Test that login fails with an incorrect password."""
        response = self.client.post(url_for('main.login'), data={
            'username': 'testuser',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Usuário ou senha inválidos', response.get_data(as_text=True))

    def test_failed_login_wrong_username(self):
        """Test that login fails with a non-existent username."""
        response = self.client.post(url_for('main.login'), data={
            'username': 'nouser',
            'password': 'testpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Usuário ou senha inválidos', response.get_data(as_text=True))

    def test_logout(self):
        """Test that a user can log out."""
        # First, log in the user
        self.client.post(url_for('main.login'), data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)

        # Then, log out
        response = self.client.get(url_for('main.logout'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Login', response.get_data(as_text=True))

    def test_access_protected_route_without_login(self):
        """Test that protected routes redirect to login when not authenticated."""
        response = self.client.get(url_for('main.dashboard'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Login', response.get_data(as_text=True))
