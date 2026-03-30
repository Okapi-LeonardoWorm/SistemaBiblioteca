import os
import tempfile

from tests.unit.base import BaseTestCase

from app.utils.bulk_import import build_template_bytes, count_data_rows, iter_rows, read_headers


class TestBulkImportReaders(BaseTestCase):
    def test_xlsx_reader_parses_headers_and_rows(self):
        headers = ['Login', 'Senha', 'NomeCompleto', 'DataNascimento']
        rows = [
            {
                'Login': 'aluno01',
                'Senha': 'senha123',
                'NomeCompleto': 'Aluno Teste',
                'DataNascimento': '11/03/2005',
            }
        ]
        content = build_template_bytes('xlsx', headers, rows)

        fd, temp_path = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd)
        try:
            with open(temp_path, 'wb') as temp_file:
                temp_file.write(content)

            loaded_headers = read_headers(temp_path, 'xlsx')
            self.assertEqual(loaded_headers, headers)

            loaded_rows = list(iter_rows(temp_path, 'xlsx'))
            self.assertEqual(len(loaded_rows), 1)
            self.assertEqual(loaded_rows[0][1]['Login'], 'aluno01')
            self.assertEqual(count_data_rows(temp_path, 'xlsx'), 1)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_xlsx_reader_ignores_blank_rows_for_count_and_iteration(self):
        headers = ['Login', 'Senha', 'NomeCompleto', 'DataNascimento']
        rows = [
            {
                'Login': 'aluno01',
                'Senha': 'senha123',
                'NomeCompleto': 'Aluno Teste',
                'DataNascimento': '11/03/2005',
            },
            {
                'Login': '   ',
                'Senha': '\t',
                'NomeCompleto': '',
                'DataNascimento': '\n',
            },
        ]
        content = build_template_bytes('xlsx', headers, rows)

        fd, temp_path = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd)
        try:
            with open(temp_path, 'wb') as temp_file:
                temp_file.write(content)

            self.assertEqual(count_data_rows(temp_path, 'xlsx'), 1)
            loaded_rows = list(iter_rows(temp_path, 'xlsx'))
            self.assertEqual(len(loaded_rows), 1)
            self.assertEqual(loaded_rows[0][1]['Login'], 'aluno01')
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
