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
        student_2 = User(
            identificationCode='ALUNO-200',
            userCompleteName='Aluno Dashboard 2',
            password='password',
            userType='aluno',
            birthDate='2008-01-01',
            gradeNumber=8,
            className='B tarde',
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
        book3 = Book(
            bookName='Livro C',
            amount=1,
            authorName='Autor C',
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

        db.session.add_all([student, student_2, collaborator, book1, book2, book3, kw1, kw2])
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
        loan_active_2 = Loan(
            amount=1,
            loanDate=date.today() - timedelta(days=2),
            returnDate=date.today() + timedelta(days=1),
            userId=student_2.userId,
            bookId=book3.bookId,
            createdBy=self.admin_user.userId,
            updatedBy=self.admin_user.userId,
            status=StatusLoan.ACTIVE,
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

        db.session.add_all([loan_active, loan_overdue, loan_active_2, loan_lost])
        db.session.commit()

    def test_dashboard_kpis(self):
        response = self.client.get('/api/dashboard/kpis')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        self.assertIn('total_books', payload['data'])

    def test_dashboard_devolucoes(self):
        response = self.client.get('/api/dashboard/devolucoes?quick_filter=all&per_page=5')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        self.assertIn('items', payload['data'])
        self.assertIn('kpis', payload['data'])
        self.assertGreaterEqual(len(payload['data']['items']), 1)
        self.assertIn('loan_id', payload['data']['items'][0])
        self.assertIn('all', payload['data']['kpis'])

    def test_dashboard_devolucoes_filtro_serie_turma(self):
        response = self.client.get('/api/dashboard/devolucoes?quick_filter=all&serie=7&turma=A%20manh%C3%A3')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        items = payload['data']['items']
        self.assertGreaterEqual(len(items), 1)
        codes = {item['student_code'] for item in items}
        self.assertEqual(codes, {'ALUNO-100'})

    def test_dashboard_devolucoes_filtro_multiplas_series(self):
        response = self.client.get('/api/dashboard/devolucoes?quick_filter=all&serie=7&serie=8')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        items = payload['data']['items']
        self.assertGreaterEqual(len(items), 2)
        codes = {item['student_code'] for item in items}
        self.assertIn('ALUNO-100', codes)
        self.assertIn('ALUNO-200', codes)

    def test_dashboard_devolucoes_filter_options(self):
        response = self.client.get('/api/dashboard/devolucoes/filter-options')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        self.assertIn(7, payload['data']['series'])
        self.assertIn(8, payload['data']['series'])
        self.assertIn('A manhã', payload['data']['turmas'])
        self.assertIn('B tarde', payload['data']['turmas'])
        self.assertIn('aluno', payload['data']['user_types'])

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
        start = (date.today() - timedelta(days=30)).isoformat()
        end = date.today().isoformat()
        response = self.client.get(f'/api/dashboard/engajamento?start_date={start}&end_date={end}&user_type=aluno')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        self.assertIn('top_alunos', payload['data'])

    def test_dashboard_engajamento_user_type_multi(self):
        start = (date.today() - timedelta(days=30)).isoformat()
        end = date.today().isoformat()
        response = self.client.get(
            f'/api/dashboard/engajamento?start_date={start}&end_date={end}&user_type=aluno&user_type=bibliotecario'
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        self.assertIn('emprestimos_por_turma', payload['data'])

    def test_dashboard_popularidade(self):
        start = (date.today() - timedelta(days=30)).isoformat()
        end = date.today().isoformat()
        response = self.client.get(
            f'/api/dashboard/popularidade?start_date={start}&end_date={end}&limit=5&user_type=aluno'
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        self.assertIn('top_livros', payload['data'])

    def test_dashboard_popularidade_user_type_multi(self):
        start = (date.today() - timedelta(days=30)).isoformat()
        end = date.today().isoformat()
        response = self.client.get(
            f'/api/dashboard/popularidade?start_date={start}&end_date={end}&limit=5&user_type=aluno&user_type=bibliotecario'
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        self.assertIn('distribuicao_tags', payload['data'])

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
