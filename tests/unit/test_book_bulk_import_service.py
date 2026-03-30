from tests.unit.base import BaseTestCase

from app.services.book_bulk_create_service import (
    _translate_single_error_message_ptbr,
    translate_error_keys_for_report,
)


class TestBookBulkImportService(BaseTestCase):
    def test_translate_number_between_error_message_to_ptbr(self):
        message = 'Number must be between 1000 and 9999.'
        translated = _translate_single_error_message_ptbr(message)
        self.assertEqual(translated, 'Numero deve estar entre 1000 e 9999.')

    def test_translate_error_keys_maps_book_labels(self):
        translated = translate_error_keys_for_report({
            'publicationYear': ['Number must be between 1000 and 9999.'],
            'acquisitionDate': ['Not a valid date value.'],
            'linha': ['Linha original: 32'],
        })

        self.assertIn('AnoPublicacao', translated)
        self.assertIn('DataAquisicao', translated)
        self.assertIn('Linha', translated)
        self.assertEqual(translated['AnoPublicacao'][0], 'Numero deve estar entre 1000 e 9999.')
        self.assertEqual(translated['DataAquisicao'][0], 'Data invalida.')

    def test_translate_error_messages_removes_redundant_range_when_integer_invalid(self):
        translated = translate_error_keys_for_report({
            'publicationYear': [
                'Not a valid integer value.',
                'Number must be between 1000 and 9999.',
            ]
        })

        self.assertEqual(translated['AnoPublicacao'], ['Numero inteiro invalido.'])
