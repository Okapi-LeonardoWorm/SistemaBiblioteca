from tests.unit.base import BaseTestCase
from flask import url_for
from datetime import date, timedelta

from app import db
from app.models import Book, KeyWord, Loan, StatusLoan, User

class TestRoutes(BaseTestCase):

    def setUp(self):
        """Extend the base setUp to create and log in an admin user."""
        super().setUp()
        self.admin_user = self._create_admin_user()
        # Log in the admin user
        self.client.post(url_for('auth.login'), data={
            'username': self.admin_user.username,
            'password': 'adminpassword' # The raw password used in the helper
        }, follow_redirects=True)

    def test_dashboard_route(self):
        """Test that the dashboard is accessible when an admin is logged in."""
        response = self.client.get(url_for('navigation.dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Dashboard Administrativo', response.get_data(as_text=True))

    def test_livros_route(self):
        """Test that the book management page is accessible."""
        response = self.client.get(url_for('books.livros'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Gerenciar Livros', response.get_data(as_text=True))

    def test_users_route(self):
        """Test that the user management page is accessible."""
        response = self.client.get(url_for('users.list_users'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Gerenciar Usuários', response.get_data(as_text=True))

    def test_emprestimos_route(self):
        """Test that the loan management page is accessible."""
        response = self.client.get(url_for('loans.emprestimos'))
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

        response = self.client.get(url_for('loans.emprestimos', search='Livro Pesquisa'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Livro Pesquisa Rota', response.get_data(as_text=True))

    def test_emprestimos_advanced_filters_route(self):
        """Advanced filters should combine with AND across loan, user and book fields."""
        user_match = User(
            identificationCode='ALUNO-001',
            userCompleteName='Aluno Filtro',
            password='password',
            userType='student',
            birthDate=date(2008, 5, 10),
            cpf='12345678901',
            rg='1234567890',
            userPhone='11999999999',
            gradeNumber=7,
            className='A',
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
        )
        user_other = User(
            identificationCode='ALUNO-999',
            userCompleteName='Outro Usuário',
            password='password',
            userType='teacher',
            birthDate=date(1990, 1, 1),
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
        )

        book_match = Book(
            bookName='Livro Avançado',
            amount=3,
            authorName='Autor Exato',
            publisherName='Editora Boa',
            publishedDate=date(2020, 1, 1),
            acquisitionDate=date(2024, 1, 10),
            description='Descrição especial para filtro',
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
            creationDate=date.today(),
            lastUpdate=date.today(),
        )
        book_other = Book(
            bookName='Livro Sem Match',
            amount=3,
            authorName='Outro Autor',
            publisherName='Outra Editora',
            publishedDate=date(2010, 1, 1),
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
            creationDate=date.today(),
            lastUpdate=date.today(),
        )

        kw_match = KeyWord(
            word='aventura',
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
        )
        book_match.keywords.append(kw_match)

        db.session.add_all([user_match, user_other, book_match, book_other, kw_match])
        db.session.commit()

        loan_match = Loan(
            amount=2,
            loanDate=date(2025, 1, 15),
            returnDate=date(2025, 1, 25),
            userId=user_match.userId,
            bookId=book_match.bookId,
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
            status=StatusLoan.ACTIVE,
        )
        loan_other = Loan(
            amount=1,
            loanDate=date(2024, 1, 15),
            returnDate=date(2024, 1, 25),
            userId=user_other.userId,
            bookId=book_other.bookId,
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
            status=StatusLoan.COMPLETED,
        )
        db.session.add_all([loan_match, loan_other])
        db.session.commit()

        response = self.client.get(url_for(
            'loans.emprestimos',
            loan_date_start='2025-01-01',
            loan_date_end='2025-12-31',
            return_date_start='2025-01-01',
            return_date_end='2025-12-31',
            loan_status='ACTIVE',
            loan_amount_min='2',
            loan_amount_max='2',
            loan_created_by='admin',
            user_code='ALUNO-001',
            user_name='Aluno Filtro',
            user_type='student',
            user_birth_start='2008-01-01',
            user_birth_end='2008-12-31',
            user_cpf='12345678901',
            user_rg='1234567890',
            user_phone='1199999',
            user_grade='7',
            user_class='A',
            book_name='Livro Avançado',
            book_author='Autor Exato',
            book_publisher='Editora Boa',
            book_published_start='2019-01-01',
            book_published_end='2021-12-31',
            book_acquired_start='2024-01-01',
            book_acquired_end='2024-12-31',
            book_description='especial',
            book_tags='aventura'
        ))

        content = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Livro Avançado', content)
        self.assertNotIn('Livro Sem Match', content)

    def test_emprestimos_filters_are_preserved_in_page_controls(self):
        """Selected advanced filters should be preserved in per-page and pagination parameters."""
        response = self.client.get(url_for(
            'loans.emprestimos',
            search='Livro',
            per_page=50,
            user_name='Maria',
            book_tags='aventura'
        ))

        content = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="user_name" value="Maria"', content)
        self.assertIn('name="book_tags" value="aventura"', content)
        self.assertIn('name="per_page"', content)
        
    def test_palavras_chave_route(self):
        """Test that the keyword management page is accessible."""
        response = self.client.get(url_for('keywords.palavras_chave'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Gerenciar Tags', response.get_data(as_text=True))

    def test_configuracoes_route(self):
        """Test that the configuration management page is accessible for admin users."""
        response = self.client.get(url_for('configs.configuracoes'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Gerenciar Configurações', response.get_data(as_text=True))

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

        response = self.client.post(url_for('loans.informar_retorno_emprestimo', loan_id=loan.loanId), data={
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

        response = self.client.post(url_for('loans.informar_retorno_emprestimo', loan_id=loan.loanId), data={
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

        response = self.client.post(url_for('loans.informar_retorno_emprestimo', loan_id=loan.loanId), data={
            'status': 'LOST',
            'returnDate': date.today().strftime('%Y-%m-%d')
        })

        self.assertEqual(response.status_code, 409)
        self.assertFalse(response.json['success'])
        self.assertIn('status', response.json['errors'])
