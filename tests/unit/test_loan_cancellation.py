import unittest
from datetime import datetime, timedelta
from app import createApp, db
from app.models import User, Book, Loan, StatusLoan, Configuration, Role
from flask import json
from flask_login import login_user

class TestLoanCancellation(unittest.TestCase):
    def setUp(self):
        self.app = createApp('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create a user to act as admin/creator
        self.user = User(
            identificationCode='testuser', 
            userCompleteName='Test User',
            userType='student',
            creationDate=datetime.now(),
            lastUpdate=datetime.now(),
            birthDate=datetime(2000, 1, 1),
            password='password123'
        )
        db.session.add(self.user)
        db.session.commit()

        # Create a user to login
        self.login_user = User(
            identificationCode='loginuser', 
            userCompleteName='Login User',
            userType='student',
            creationDate=datetime.now(),
            lastUpdate=datetime.now(),
            birthDate=datetime(2000, 1, 1),
            password='password123'
        )
        db.session.add(self.login_user)
        db.session.commit()
        
        # Create book
        self.book = Book(
            bookName='Test Book', 
            amount=10, 
            creationDate=datetime.now(), 
            lastUpdate=datetime.now(),
            createdBy=self.user.userId,
            updatedBy=self.user.userId
        )
        db.session.add(self.book)
        db.session.commit()

        # Insert Config
        config = Configuration(
            key='TEMPO_MAXIMO_PARA_CANCELAMENTO_DE_EMPRESTIMO',
            value='240', # 4 hours
            description='Test config',
            creationDate=datetime.now(),
            lastUpdate=datetime.now(),
            createdBy=self.user.userId,
            updatedBy=self.user.userId
        )
        db.session.add(config)
        db.session.commit()
        
        self.client = self.app.test_client()

        # Manually log in via session
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.login_user.userId)
            sess['userType'] = 'student'

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_cancel_active_loan_within_limit(self):
        """
        Teste Bruto: Validar cancelamento bem-sucedido dentro do prazo.
        """
        loan = Loan(
            amount=1,
            loanDate=datetime.now(),
            returnDate=datetime.now() + timedelta(days=7),
            userId=self.user.userId,
            bookId=self.book.bookId,
            creationDate=datetime.now(), # NOW
            lastUpdate=datetime.now(),
            createdBy=self.user.userId,
            updatedBy=self.user.userId,
            status=StatusLoan.ACTIVE
        )
        db.session.add(loan)
        db.session.commit()

        response = self.client.post(f'/emprestimos/cancel/{loan.loanId}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        updated_loan = Loan.query.get(loan.loanId)
        self.assertEqual(updated_loan.status, StatusLoan.CANCELLED)

    def test_cancel_future_loan_client_ahead(self):
        """
        Simula 'Cliente Adiantado' / 'Servidor Atrasado'.
        A data de criação está no FUTURO em relação ao servidor.
        Isso resulta em um tempo decorrido negativo.
        Logicamente deve ser permitido cancelar (já que negativo < limite).
        """
        future_time = datetime.now() + timedelta(hours=2) # 2 hours in future
        
        loan = Loan(
            amount=1,
            loanDate=datetime.now(),
            returnDate=datetime.now() + timedelta(days=7),
            userId=self.user.userId,
            bookId=self.book.bookId,
            creationDate=future_time,
            lastUpdate=datetime.now(),
            createdBy=self.user.userId,
            updatedBy=self.user.userId,
            status=StatusLoan.ACTIVE
        )
        db.session.add(loan)
        db.session.commit()

        response = self.client.post(f'/emprestimos/cancel/{loan.loanId}', follow_redirects=True)
        
        # Should succeed because (now - future) is negative, which is < 240
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

    def test_cancel_old_loan_client_behind(self):
        """
        Simula 'Cliente Atrasado' / 'Servidor Adiantado' (Tempo Excedido).
        A data de criação está no PASSADO além do limite permitido.
        Isso resulta em tempo decorrido > limite.
        Deve ser bloqueado.
        """
        past_time = datetime.now() - timedelta(minutes=241) # 4 hours + 1 min ago
        
        loan = Loan(
            amount=1,
            loanDate=datetime.now(),
            returnDate=datetime.now() + timedelta(days=7),
            userId=self.user.userId,
            bookId=self.book.bookId,
            creationDate=past_time,
            lastUpdate=datetime.now(),
            createdBy=self.user.userId,
            updatedBy=self.user.userId,
            status=StatusLoan.ACTIVE
        )
        db.session.add(loan)
        db.session.commit()

        response = self.client.post(f'/emprestimos/cancel/{loan.loanId}', follow_redirects=True)
        
        # Should fail with 403
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('Tempo limite para cancelamento excedido', data['message'])

if __name__ == '__main__':
    unittest.main()
