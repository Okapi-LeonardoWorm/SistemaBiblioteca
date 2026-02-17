from tests.unit.base import BaseTestCase
from flask import url_for
from app.models import User, Book, Loan, KeyWord, StatusLoan
from app import db, bcrypt
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
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['success'])

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
        self.assertIn('Usuário registrado com sucesso!', response_staff.get_data(as_text=True))
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
        self.assertIn('Usuário registrado com sucesso!', response_admin.get_data(as_text=True))
        new_admin_user = User.query.filter_by(username='newadmin').first()
        self.assertIsNotNone(new_admin_user)
        self.assertEqual(new_admin_user.userType, 'admin')

    def test_register_trims_and_lowercases_identification_code(self):
        """Register should normalize username to trimmed lower-case identification code."""
        response = self.client.post(url_for('main.register'), data={
            'username': '  UserMixedCase  ',
            'password': 'password123',
            'userType': 'student',
            'birthDate': '2001-02-03'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        created_user = User.query.filter_by(identificationCode='usermixedcase').first()
        self.assertIsNotNone(created_user)
        self.assertEqual(created_user.userCompleteName, 'UserMixedCase')

    def test_register_sanitizes_phone_cpf_and_rg_to_digits(self):
        """Register validators should keep only digits for phone/CPF/RG fields."""
        response = self.client.post(url_for('main.register'), data={
            'username': 'digits_only_user',
            'password': 'password123',
            'userType': 'student',
            'birthDate': '2001-02-03',
            'userPhone': '(11) 91234-5678',
            'cpf': '123.456.789-01',
            'rg': '12.345.678-9'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        created_user = User.query.filter_by(identificationCode='digits_only_user').first()
        self.assertIsNotNone(created_user)
        self.assertEqual(created_user.userPhone, '11912345678')
        self.assertEqual(created_user.cpf, '12345678901')
        self.assertEqual(created_user.rg, '123456789')

    def test_create_user_rejects_invalid_phone_length(self):
        """/users/new should reject phone values that do not have 10 or 11 digits."""
        response = self.client.post(url_for('main.new_user'), data={
            'identificationCode': 'invalid_phone_user',
            'userCompleteName': 'Invalid Phone User',
            'userType': 'aluno',
            'birthDate': '2003-03-03',
            'userPhone': '12345'
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json['success'])
        self.assertIn('userPhone', response.json['errors'])

    def test_create_user_requires_birthdate(self):
        """/users/new should fail in create mode when birthDate is missing."""
        response = self.client.post(url_for('main.new_user'), data={
            'identificationCode': 'no_birth_user',
            'userCompleteName': 'User Without Birth',
            'userType': 'aluno'
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json['success'])
        self.assertIn('birthDate', response.json['errors'])

    def test_create_user_rejects_duplicate_identification_code(self):
        """/users/new should reject duplicate identificationCode values."""
        existing = User(
            identificationCode='dup_code',
            password='password',
            userType='aluno',
            userCompleteName='Existing User',
            birthDate=date(2002, 1, 1),
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
        )
        db.session.add(existing)
        db.session.commit()

        response = self.client.post(url_for('main.new_user'), data={
            'identificationCode': 'dup_code',
            'userCompleteName': 'Duplicated User',
            'userType': 'aluno',
            'birthDate': '2003-01-01'
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json['success'])
        self.assertIn('identificationCode', response.json['errors'])

    def test_edit_user_keeps_password_when_blank(self):
        """/users/edit should keep current password when password field is empty."""
        user = User(
            identificationCode='edit_pwd_user',
            userCompleteName='User Edit Password',
            password='current_password',
            userType='aluno',
            birthDate=date(2004, 4, 4),
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
        )
        db.session.add(user)
        db.session.commit()

        response = self.client.post(url_for('main.edit_user', user_id=user.userId), data={
            'identificationCode': 'edit_pwd_user',
            'userCompleteName': 'User Edit Password Updated',
            'userType': 'aluno',
            'birthDate': '2004-04-04',
            'password': ''
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['success'])

        updated_user = User.query.get(user.userId)
        self.assertEqual(updated_user.password, 'current_password')

    def test_edit_user_updates_password_when_provided(self):
        """/users/edit should hash and update password when a new one is provided."""
        user = User(
            identificationCode='edit_pwd_user2',
            userCompleteName='User Edit Password 2',
            password='current_password',
            userType='aluno',
            birthDate=date(2004, 4, 5),
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
        )
        db.session.add(user)
        db.session.commit()

        response = self.client.post(url_for('main.edit_user', user_id=user.userId), data={
            'identificationCode': 'edit_pwd_user2',
            'userCompleteName': 'User Edit Password Updated 2',
            'userType': 'aluno',
            'birthDate': '2004-04-05',
            'password': 'newpass123'
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['success'])

        updated_user = User.query.get(user.userId)
        self.assertNotEqual(updated_user.password, 'current_password')
        self.assertTrue(bcrypt.check_password_hash(updated_user.password, 'newpass123'))

    def test_create_book_trims_text_fields(self):
        """/livros/new should trim trailing and leading spaces in text fields."""
        response = self.client.post(url_for('main.novo_livro'), data={
            'bookName': '  Livro com Espaço  ',
            'authorName': '  Autor com Espaço  ',
            'amount': 5,
            'keyWords': 'python'
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['success'])
        book = Book.query.filter_by(bookName='Livro com Espaço').first()
        self.assertIsNotNone(book)
        self.assertEqual(book.authorName, 'Autor com Espaço')

    def test_create_book_rejects_zero_amount(self):
        """/livros/new should reject zero quantity."""
        response = self.client.post(url_for('main.novo_livro'), data={
            'bookName': 'Livro Inválido',
            'amount': 0,
            'keyWords': 'python'
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json['success'])
        self.assertIn('amount', response.json['errors'])

    def test_create_loan(self):
        """Test loan creation via the /emprestimos/new endpoint."""
        student = User(username='teststudent', password='password', userType='student', birthDate=date(2005, 5, 5), createdBy=self.admin_user.userId, updatedBy=self.admin_user.userId)
        book = Book(bookName='Loanable Book', amount=1, createdBy=self.admin_user.userId, updatedBy=self.admin_user.userId, creationDate=date.today(), lastUpdate=date.today())
        db.session.add_all([student, book])
        db.session.commit()

        response = self.client.post(url_for('main.novo_emprestimo'), data={
            'userId': student.userId,
            'bookId': book.bookId,
            'amount': 1,
            'loanDate': date.today().strftime('%Y-%m-%d'),
            'returnDate': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d')
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['success'])

        loan = Loan.query.filter_by(userId=student.userId, bookId=book.bookId).first()
        self.assertIsNotNone(loan)
        self.assertEqual(loan.status, StatusLoan.ACTIVE)

    def test_create_loan_rejects_return_date_before_loan_date(self):
        """/emprestimos/new should reject returnDate earlier than loanDate."""
        student = User(username='loan_invalid_date', password='password', userType='student', birthDate=date(2005, 5, 5), createdBy=self.admin_user.userId, updatedBy=self.admin_user.userId)
        book = Book(bookName='Livro Datas', amount=2, createdBy=self.admin_user.userId, updatedBy=self.admin_user.userId, creationDate=date.today(), lastUpdate=date.today())
        db.session.add_all([student, book])
        db.session.commit()

        response = self.client.post(url_for('main.novo_emprestimo'), data={
            'userId': student.userId,
            'bookId': book.bookId,
            'amount': 1,
            'loanDate': date.today().strftime('%Y-%m-%d'),
            'returnDate': (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json['success'])

    def test_create_loan_rejects_nonexistent_user(self):
        """/emprestimos/new should reject userId values that do not exist."""
        book = Book(bookName='Livro Sem Usuário', amount=1, createdBy=self.admin_user.userId, updatedBy=self.admin_user.userId, creationDate=date.today(), lastUpdate=date.today())
        db.session.add(book)
        db.session.commit()

        response = self.client.post(url_for('main.novo_emprestimo'), data={
            'userId': 99999,
            'bookId': book.bookId,
            'amount': 1,
            'loanDate': date.today().strftime('%Y-%m-%d'),
            'returnDate': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d')
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json['success'])

    def test_create_loan_rejects_when_overlapping_loans_exhaust_stock(self):
        """/emprestimos/new should reject loan if overlapping active loans consume all stock."""
        student1 = User(username='student_overlap_1', password='password', userType='student', birthDate=date(2005, 5, 1), createdBy=self.admin_user.userId, updatedBy=self.admin_user.userId)
        student2 = User(username='student_overlap_2', password='password', userType='student', birthDate=date(2005, 5, 2), createdBy=self.admin_user.userId, updatedBy=self.admin_user.userId)
        book = Book(bookName='Livro Estoque Curto', amount=1, createdBy=self.admin_user.userId, updatedBy=self.admin_user.userId, creationDate=date.today(), lastUpdate=date.today())
        db.session.add_all([student1, student2, book])
        db.session.commit()

        existing_loan = Loan(
            amount=1,
            loanDate=date.today(),
            returnDate=date.today() + timedelta(days=7),
            userId=student1.userId,
            bookId=book.bookId,
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
            status=StatusLoan.ACTIVE,
        )
        db.session.add(existing_loan)
        db.session.commit()

        response = self.client.post(url_for('main.novo_emprestimo'), data={
            'userId': student2.userId,
            'bookId': book.bookId,
            'amount': 1,
            'loanDate': date.today().strftime('%Y-%m-%d'),
            'returnDate': (date.today() + timedelta(days=5)).strftime('%Y-%m-%d')
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json['success'])
        self.assertIn('validation', response.json['errors'])

    def test_create_keywords_normalizes_accents_special_chars_and_deduplicates(self):
        """/palavras_chave/new should normalize and deduplicate submitted tags."""
        response = self.client.post(url_for('main.nova_palavra_chave'), data={
            'word': ' ciência!! ; ciência ; ai-ml '
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['success'])
        self.assertEqual(response.json['created'], 2)

        self.assertIsNotNone(KeyWord.query.filter_by(word='CIENCIA').first())
        self.assertIsNotNone(KeyWord.query.filter_by(word='AI-ML').first())

    def test_edit_keyword_rejects_duplicate_after_normalization(self):
        """/palavras_chave/edit should reject updates that normalize to an existing keyword."""
        kw1 = KeyWord(word='CIENCIA', createdBy=self.admin_user.userId, updatedBy=self.admin_user.userId)
        kw2 = KeyWord(word='LITERATURA', createdBy=self.admin_user.userId, updatedBy=self.admin_user.userId)
        db.session.add_all([kw1, kw2])
        db.session.commit()

        response = self.client.post(url_for('main.editar_palavra_chave', keyword_id=kw2.wordId), data={
            'word': 'ciência'
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json['success'])
        self.assertIn('word', response.json['errors'])
