from datetime import date
from tests.unit.base import BaseTestCase
from app import db
from app.models import User, Book, Loan, KeyWord, StatusLoan

class TestModels(BaseTestCase):

    def test_user_creation(self):
        """Test that a user can be created."""
        u = User(username='testuser', password='password', userType='student', birthDate=date(2000, 1, 1))
        db.session.add(u)
        db.session.commit()
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'testuser')

    def test_book_creation(self):
        """Test that a book can be created."""
        admin = self._create_admin_user()
        b = Book(
            bookName='The Hitchhiker\'s Guide to the Galaxy',
            amount=42,
            createdBy=admin.userId,
            updatedBy=admin.userId,
            creationDate=date.today(),
            lastUpdate=date.today()
        )
        db.session.add(b)
        db.session.commit()
        self.assertEqual(Book.query.count(), 1)
        self.assertEqual(Book.query.first().amount, 42)

    def test_loan_creation_and_relationship(self):
        """Test that a loan can be created and is related to a user and a book."""
        admin = self._create_admin_user()
        student = User(username='student', password='password', userType='student', birthDate=date(2005, 5, 5))
        book = Book(
            bookName='Dune',
            amount=1,
            createdBy=admin.userId,
            updatedBy=admin.userId,
            creationDate=date.today(),
            lastUpdate=date.today()
        )
        db.session.add_all([student, book])
        db.session.commit()

        loan = Loan(
            userId=student.userId,
            bookId=book.bookId,
            amount=1,
            loanDate=date.today(),
            returnDate=date(2025, 1, 1),
            status=StatusLoan.ACTIVE,
            createdBy=admin.userId,
            updatedBy=admin.userId,
            creationDate=date.today(),
            lastUpdate=date.today()
        )
        db.session.add(loan)
        db.session.commit()
        
        # Test loan creation
        self.assertEqual(Loan.query.count(), 1)
        
        # Test relationships
        self.assertEqual(student.loans[0].book.bookName, 'Dune')
        self.assertEqual(book.loans[0].user.username, 'student')
