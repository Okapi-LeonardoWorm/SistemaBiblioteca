from tests.unit.base import BaseTestCase

from app.services.user_bulk_create_service import (
    canonicalize_header,
    format_birth_date_for_form,
    normalize_optional,
    parse_pcd,
    _translate_single_error_message_ptbr,
    translate_error_keys_for_report,
)


class TestUserBulkImportService(BaseTestCase):
    def test_parse_pcd_accepts_sim(self):
        ok, value, error = parse_pcd('sim')
        self.assertTrue(ok)
        self.assertTrue(value)
        self.assertIsNone(error)

    def test_parse_pcd_accepts_nao_or_blank(self):
        ok1, value1, _ = parse_pcd('nao')
        ok2, value2, _ = parse_pcd('   \n\t')
        self.assertTrue(ok1)
        self.assertFalse(value1)
        self.assertTrue(ok2)
        self.assertFalse(value2)

    def test_parse_pcd_rejects_unknown_text(self):
        ok, _, error = parse_pcd('talvez')
        self.assertFalse(ok)
        self.assertIn('PCD', error)

    def test_normalize_optional_cleans_whitespace(self):
        self.assertEqual(normalize_optional('  valor  '), 'valor')
        self.assertEqual(normalize_optional('   \n\t'), '')

    def test_canonicalize_header_removes_accents_and_spaces(self):
        self.assertEqual(canonicalize_header(' Código de Identificação '), 'codigo_de_identificacao')

    def test_birth_date_conversion_accepts_dd_mm_yyyy(self):
        self.assertEqual(format_birth_date_for_form('11/03/2006'), '2006-03-11')

    def test_birth_date_conversion_keeps_unknown_format_for_form_error(self):
        self.assertEqual(format_birth_date_for_form('2006/03/11'), '2006/03/11')

    def test_error_keys_are_translated_to_ptbr_labels(self):
        translated = translate_error_keys_for_report({
            'identificationCode': ['Obrigatorio'],
            'birthDate': ['Formato invalido'],
            'linha': ['Linha original: 2'],
            'database': ['Erro de banco'],
        })

        self.assertIn('Login', translated)
        self.assertIn('DataNascimento', translated)
        self.assertIn('Linha', translated)
        self.assertIn('BancoDeDados', translated)

    def test_translate_length_error_message_to_ptbr(self):
        message = 'Field must be between 4 and 80 characters long.'
        translated = _translate_single_error_message_ptbr(message)
        self.assertEqual(translated, 'Campo deve ter entre 4 e 80 caracteres.')

    def test_translate_required_error_message_to_ptbr(self):
        message = 'This field is required.'
        translated = _translate_single_error_message_ptbr(message)
        self.assertEqual(translated, 'Este campo é obrigatório.')
