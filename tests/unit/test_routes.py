from tests.unit.base import BaseTestCase
from flask import url_for
from datetime import date, timedelta

from app import db
from app.models import Book, Loan, StatusLoan, User

class TestRoutes(BaseTestCase):

    def setUp(self):
        """Extend the base setUp to create and log in an admin user."""
        super().setUp()
        self.admin_user = self._create_admin_user()
        # Log in the admin user
        self.client.post(url_for('main.login'), data={
            'username': self.admin_user.username,
            'password': 'adminpassword' # The raw password used in the helper
        }, follow_redirects=True)

    def test_dashboard_route(self):
        """Test that the dashboard is accessible when an admin is logged in."""
        response = self.client.get(url_for('main.dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Dashboard Administrativo', response.get_data(as_text=True))

    def test_livros_route(self):
        """Test that the book management page is accessible."""
        response = self.client.get(url_for('main.livros'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Gerenciar Livros', response.get_data(as_text=True))

    def test_users_route(self):
        """Test that the user management page is accessible."""
        response = self.client.get(url_for('main.list_users'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Gerenciar Usuários', response.get_data(as_text=True))

    def test_emprestimos_route(self):
        """Test that the loan management page is accessible."""
        response = self.client.get(url_for('main.emprestimos'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Gerenciar Empréstimos', response.get_data(as_text=True))

    def test_emprestimos_search_route(self):
        """Test that loan search works without query join issues."""
        student = User(
            username='student_search',
            password='password',
            userType='student',
            birthDate=date(2006, 1, 1),
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
        )
        book = Book(
            bookName='Livro Pesquisa Rota',
            amount=2,
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
            creationDate=date.today(),
            lastUpdate=date.today(),
        )
        db.session.add_all([student, book])
        db.session.commit()

        loan = Loan(
            amount=1,
            loanDate=date.today(),
            returnDate=date.today() + timedelta(days=7),
            userId=student.userId,
            bookId=book.bookId,
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
            status=StatusLoan.ACTIVE,
        )
        db.session.add(loan)
        db.session.commit()

        response = self.client.get(url_for('main.emprestimos', search='Livro Pesquisa'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Livro Pesquisa Rota', response.get_data(as_text=True))
        
    def test_palavras_chave_route(self):
        """Test that the keyword management page is accessible."""
        response = self.client.get(url_for('main.palavras_chave'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Gerenciar Tags', response.get_data(as_text=True))

    def test_return_loan_rejects_invalid_status(self):
        """Return endpoint should reject statuses other than COMPLETED and LOST."""
        student = User(
            username='student_return_invalid_status',
            password='password',
            userType='student',
            birthDate=date(2006, 1, 2),
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
        )
        book = Book(
            bookName='Livro Retorno Inválido',
            amount=2,
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
            creationDate=date.today(),
            lastUpdate=date.today(),
        )
        db.session.add_all([student, book])
        db.session.commit()

        loan = Loan(
            amount=1,
            loanDate=date.today(),
            returnDate=date.today() + timedelta(days=7),
            userId=student.userId,
            bookId=book.bookId,
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
            status=StatusLoan.ACTIVE,
        )
        db.session.add(loan)
        db.session.commit()

        response = self.client.post(url_for('main.informar_retorno_emprestimo', loan_id=loan.loanId), data={
            'status': 'ACTIVE',
            'returnDate': date.today().strftime('%Y-%m-%d')
        })

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json['success'])
        self.assertIn('status', response.json['errors'])

    def test_return_loan_rejects_date_before_loan_date(self):
        """Return endpoint should reject returnDate earlier than the loan date."""
        student = User(
            username='student_return_invalid_date',
            password='password',
            userType='student',
            birthDate=date(2006, 1, 3),
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
        )
        book = Book(
            bookName='Livro Retorno Data',
            amount=2,
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
            creationDate=date.today(),
            lastUpdate=date.today(),
        )
        db.session.add_all([student, book])
        db.session.commit()

        loan = Loan(
            amount=1,
            loanDate=date.today(),
            returnDate=date.today() + timedelta(days=7),
            userId=student.userId,
            bookId=book.bookId,
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
            status=StatusLoan.ACTIVE,
        )
        db.session.add(loan)
        db.session.commit()

        response = self.client.post(url_for('main.informar_retorno_emprestimo', loan_id=loan.loanId), data={
            'status': 'COMPLETED',
            'returnDate': (loan.loanDate - timedelta(days=1)).strftime('%Y-%m-%d')
        })

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json['success'])
        self.assertIn('returnDate', response.json['errors'])

    def test_return_loan_rejects_already_finalized(self):
        """Return endpoint should reject loans already finalized as COMPLETED/LOST."""
        student = User(
            username='student_return_finalized',
            password='password',
            userType='student',
            birthDate=date(2006, 1, 4),
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
        )
        book = Book(
            bookName='Livro Retorno Finalizado',
            amount=2,
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
            creationDate=date.today(),
            lastUpdate=date.today(),
        )
        db.session.add_all([student, book])
        db.session.commit()

        loan = Loan(
            amount=1,
            loanDate=date.today() - timedelta(days=5),
            returnDate=date.today() - timedelta(days=1),
            userId=student.userId,
            bookId=book.bookId,
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
            status=StatusLoan.COMPLETED,
        )
        db.session.add(loan)
        db.session.commit()

        response = self.client.post(url_for('main.informar_retorno_emprestimo', loan_id=loan.loanId), data={
            'status': 'LOST',
            'returnDate': date.today().strftime('%Y-%m-%d')
        })

        self.assertEqual(response.status_code, 409)
        self.assertFalse(response.json['success'])
        self.assertIn('status', response.json['errors'])
