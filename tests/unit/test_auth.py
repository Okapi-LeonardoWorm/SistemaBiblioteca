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

    def _create_login_user(self, identifier, plain_password='testpassword'):
        hashed_password = bcrypt.generate_password_hash(plain_password).decode('utf-8')
        user = User(
            identificationCode=identifier,
            password=hashed_password,
            userType='student',
            birthDate='2000-01-01',
            createdBy=1,
            updatedBy=1,
        )
        db.session.add(user)
        db.session.commit()
        return user

    def test_login_page_loads(self):
        """Test that the login page loads correctly."""
        response = self.client.get(url_for('auth.login'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Login', response.get_data(as_text=True))

    def test_successful_login(self):
        """Test that a user can log in successfully."""
        response = self.client.post(url_for('auth.login'), data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Olá, testuser!', response.get_data(as_text=True))

    def test_failed_login_wrong_password(self):
        """Test that login fails with an incorrect password."""
        response = self.client.post(url_for('auth.login'), data={
            'username': 'testuser',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Usuário ou senha inválidos', response.get_data(as_text=True))

    def test_failed_login_wrong_username(self):
        """Test that login fails with a non-existent username."""
        response = self.client.post(url_for('auth.login'), data={
            'username': 'nouser',
            'password': 'testpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Usuário ou senha inválidos', response.get_data(as_text=True))

    def test_deleted_user_cannot_login(self):
        """Users marked as deleted must not authenticate."""
        user = User.query.filter_by(username='testuser').first()
        user.deleted = True
        db.session.commit()

        response = self.client.post(url_for('auth.login'), data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Usuário ou senha inválidos', response.get_data(as_text=True))

    def test_login_accepts_username_with_extra_spaces(self):
        """Login should normalize username removendo espaços nas extremidades."""
        response = self.client.post(url_for('auth.login'), data={
            'username': '  testuser  ',
            'password': 'testpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Olá, testuser!', response.get_data(as_text=True))

    def test_login_accepts_email_identifier_case_insensitive(self):
        """Login should accept email identifier and compare case-insensitively."""
        self._create_login_user('test.user+alias@example.com', plain_password='emailpassword')

        response = self.client.post(url_for('auth.login'), data={
            'username': '  TEST.USER+ALIAS@EXAMPLE.COM  ',
            'password': 'emailpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Olá, test.user+alias@example.com!', response.get_data(as_text=True))

    def test_login_accepts_long_identifier(self):
        """Login should accept identifiers longer than 20 chars up to model/form limit."""
        long_identifier = 'user_' + ('a' * 60)
        self._create_login_user(long_identifier, plain_password='longpassword')

        response = self.client.post(url_for('auth.login'), data={
            'username': long_identifier,
            'password': 'longpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(f'Olá, {long_identifier}!', response.get_data(as_text=True))

    def test_logged_admin_accessing_login_is_redirected_to_dashboard(self):
        """Authenticated admin should not access login page and must be redirected to dashboard."""
        hashed_password = bcrypt.generate_password_hash('adminpassword').decode('utf-8')
        admin_user = User(
            identificationCode='adminuser',
            password=hashed_password,
            userType='admin',
            birthDate='1990-01-01',
            createdBy=1,
            updatedBy=1,
        )
        db.session.add(admin_user)
        db.session.commit()

        self.client.post(url_for('auth.login'), data={
            'username': 'adminuser',
            'password': 'adminpassword'
        }, follow_redirects=True)

        response = self.client.get(url_for('auth.login'), follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn(url_for('navigation.dashboard', _external=False), response.headers.get('Location', ''))

    def test_logged_non_admin_accessing_login_is_redirected_to_menu(self):
        """Authenticated non-admin should not access login page and must be redirected to menu."""
        self.client.post(url_for('auth.login'), data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)

        response = self.client.get(url_for('auth.login'), follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn(url_for('navigation.menu', _external=False), response.headers.get('Location', ''))

    def test_logout(self):
        """Test that a user can log out."""
        # First, log in the user
        self.client.post(url_for('auth.login'), data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)

        # Then, log out
        response = self.client.get(url_for('auth.logout'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Login', response.get_data(as_text=True))

    def test_access_protected_route_without_login(self):
        """Test that protected routes redirect to login when not authenticated."""
        response = self.client.get(url_for('navigation.dashboard'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Login', response.get_data(as_text=True))
