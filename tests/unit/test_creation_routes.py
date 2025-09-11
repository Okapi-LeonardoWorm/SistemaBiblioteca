from tests.unit.base import BaseTestCase
from flask import url_for
from app.models import User, Book, Loan, StatusLoan
from app import db
from datetime import date, timedelta

class TestCreationRoutes(BaseTestCase):

    def setUp(self):
        """Sets up the test environment before each test."""
        super().setUp()
        self.admin_user = self._create_admin_user()
        # Log in the admin user for routes that require authentication
        self.client.post(url_for('main.login'), data={
            'username': 'admin',
            'password': 'adminpassword'
        }, follow_redirects=True)

    def test_create_book(self):
        """Test book creation via the /livros/new endpoint."""
        response = self.client.post(url_for('main.novo_livro'), data={
            'bookName': 'New Test Book',
            'authorName': 'Test Author',
            'amount': 10,
            'publishedDate': '2024-01-01',
            'acquisitionDate': '2024-01-01',
            'keyWords': 'test; python; flask'
        }, follow_redirects=True)
        
        # Check if the response is a success JSON
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['success'])

        # Check if the book was actually created in the database
        book = Book.query.filter_by(bookName='New Test Book').first()
        self.assertIsNotNone(book)
        self.assertEqual(book.amount, 10)

    def test_create_users_via_register(self):
        """Test creation of different user types via the /register endpoint."""
        # 1. Admin creates a staff member
        response_staff = self.client.post(url_for('main.register'), data={
            'username': 'staffuser',
            'password': 'password123',
            'userType': 'staff',
            'birthDate': '1995-05-05'
        }, follow_redirects=True)
        self.assertEqual(response_staff.status_code, 200)
        self.assertIn(b'Usuário registrado com sucesso!', response_staff.data)
        staff_user = User.query.filter_by(username='staffuser').first()
        self.assertIsNotNone(staff_user)
        self.assertEqual(staff_user.userType, 'staff')

        # 2. Admin creates another admin
        response_admin = self.client.post(url_for('main.register'), data={
            'username': 'newadmin',
            'password': 'password123',
            'userType': 'admin',
            'birthDate': '1990-01-01'
        }, follow_redirects=True)
        self.assertEqual(response_admin.status_code, 200)
        self.assertIn(b'Usuário registrado com sucesso!', response_admin.data)
        new_admin_user = User.query.filter_by(username='newadmin').first()
        self.assertIsNotNone(new_admin_user)
        self.assertEqual(new_admin_user.userType, 'admin')

    def test_create_loan(self):
        """Test loan creation via the /emprestimos/new endpoint."""
        # First, create a student and a book to be loaned
        student = User(username='teststudent', password='password', userType='student', birthDate=date(2005, 5, 5))
        book = Book(bookName='Loanable Book', amount=1, createdBy=self.admin_user.userId, updatedBy=self.admin_user.userId, creationDate=date.today(), lastUpdate=date.today())
        db.session.add_all([student, book])
        db.session.commit()

        response = self.client.post(url_for('main.novo_emprestimo'), data={
            'userId': student.userId,
            'bookId': book.bookId,
            'amount': 1,
            'loanDate': date.today().strftime('%Y-%m-%d'),
            'returnDate': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d')
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['success'])

        # Check if the loan was created in the database
        loan = Loan.query.filter_by(userId=student.userId, bookId=book.bookId).first()
        self.assertIsNotNone(loan)
        self.assertEqual(loan.status, StatusLoan.ACTIVE)
