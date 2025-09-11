from tests.unit.base import BaseTestCase
from flask import url_for

class TestRoutes(BaseTestCase):

    def setUp(self):
        """Extend the base setUp to create and log in an admin user."""
        super().setUp()
        self._create_admin_user()
        # Log in the admin user
        self.client.post(url_for('main.login'), data={
            'username': 'admin',
            'password': 'adminpassword'
        }, follow_redirects=True)

    def test_dashboard_route(self):
        """Test that the dashboard is accessible when an admin is logged in."""
        response = self.client.get(url_for('main.dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard Administrativo', response.data)

    def test_livros_route(self):
        """Test that the book management page is accessible."""
        response = self.client.get(url_for('main.livros'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Gerenciar Livros', response.data)

    def test_users_route(self):
        """Test that the user management page is accessible."""
        response = self.client.get(url_for('main.list_users'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Gerenciar Usuários', response.data)

    def test_emprestimos_route(self):
        """Test that the loan management page is accessible."""
        response = self.client.get(url_for('main.emprestimos'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Gerenciar Empréstimos', response.data)
        
    def test_palavras_chave_route(self):
        """Test that the keyword management page is accessible."""
        response = self.client.get(url_for('main.palavras_chave'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Gerenciar Tags', response.data)
