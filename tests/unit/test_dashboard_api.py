from datetime import date, timedelta

from app import db
from app.models import Book, KeyWord, Loan, StatusLoan, User
from tests.unit.base import BaseTestCase


class TestDashboardApi(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.admin_user = self._create_admin_user()
        self.client.post('/login', data={
            'username': self.admin_user.username,
            'password': 'adminpassword',
        }, follow_redirects=True)
        self._seed_data()

    def _seed_data(self):
        student = User(
            identificationCode='ALUNO-100',
            userCompleteName='Aluno Dashboard',
            password='password',
            userType='aluno',
            birthDate='2009-01-01',
            gradeNumber=7,
            className='A manhã',
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
        )
        collaborator = User(
            identificationCode='COL-200',
            userCompleteName='Colaborador Dashboard',
            password='password',
            userType='bibliotecario',
            birthDate='1990-01-01',
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
        )

        book1 = Book(
            bookName='Livro A',
            amount=3,
            authorName='Autor A',
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
            creationDate=date.today(),
            lastUpdate=date.today(),
        )
        book2 = Book(
            bookName='Livro B',
            amount=2,
            authorName='Autor B',
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
            creationDate=date.today(),
            lastUpdate=date.today(),
        )

        kw1 = KeyWord(
            word='aventura',
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
        )
        kw2 = KeyWord(
            word='ficcao',
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
        )

        book1.keywords.extend([kw1, kw2])
        book2.keywords.append(kw1)

        db.session.add_all([student, collaborator, book1, book2, kw1, kw2])
        db.session.commit()

        loan_active = Loan(
            amount=1,
            loanDate=date.today() - timedelta(days=1),
            returnDate=date.today(),
            userId=student.userId,
            bookId=book1.bookId,
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
            status=StatusLoan.ACTIVE,
        )
        loan_overdue = Loan(
            amount=1,
            loanDate=date.today() - timedelta(days=20),
            returnDate=date.today() - timedelta(days=10),
            userId=student.userId,
            bookId=book2.bookId,
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
            status=StatusLoan.OVERDUE,
        )
        loan_lost = Loan(
            amount=1,
            loanDate=date.today() - timedelta(days=50),
            returnDate=date.today() - timedelta(days=35),
            userId=student.userId,
            bookId=book2.bookId,
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
            status=StatusLoan.LOST,
        )

        db.session.add_all([loan_active, loan_overdue, loan_lost])
        db.session.commit()

    def test_dashboard_kpis(self):
        response = self.client.get('/api/dashboard/kpis')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        self.assertIn('total_books', payload['data'])

    def test_dashboard_devolucoes(self):
        response = self.client.get('/api/dashboard/devolucoes?quick_filter=pending&per_page=5')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        self.assertIn('items', payload['data'])
        self.assertIn('kpis', payload['data'])
        self.assertGreaterEqual(len(payload['data']['items']), 1)
        self.assertIn('loan_id', payload['data']['items'][0])

    def test_dashboard_tags_top(self):
        response = self.client.get('/api/dashboard/tags-top?limit=10')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        self.assertGreaterEqual(len(payload['data']['items']), 1)

    def test_dashboard_ultimos_emprestimos(self):
        response = self.client.get('/api/dashboard/ultimos-emprestimos?limit=10')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        self.assertIn('items', payload['data'])

    def test_dashboard_engajamento(self):
        response = self.client.get('/api/dashboard/engajamento?period=month')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        self.assertIn('top_alunos', payload['data'])

    def test_dashboard_popularidade(self):
        response = self.client.get('/api/dashboard/popularidade?range=anual&limit=5')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        self.assertIn('top_livros', payload['data'])

    def test_dashboard_acervo(self):
        response = self.client.get('/api/dashboard/acervo?days_lost=30&limit=10')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        self.assertIn('lost_count', payload['data'])
        self.assertGreaterEqual(len(payload['data']['items']), 1)
        self.assertIn('loan_id', payload['data']['items'][0])

    def test_dashboard_drilldown(self):
        response = self.client.get('/api/dashboard/drilldown?source=tags_top&label=aventura')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        self.assertIn('title', payload['data'])
        self.assertIn('items', payload['data'])
