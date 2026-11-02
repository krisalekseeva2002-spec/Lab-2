import unittest
from core import build_result, classify_document, extract_fields, find_valid_date


class DocumentTests(unittest.TestCase):
    def test_passport_classification_and_fields(self):
        lines = [
            'ПАСПОРТ УЧЕБНЫЙ МАКЕТ',
            'РОССИЙСКАЯ ФЕДЕРАЦИЯ',
            'Фамилия: Тестов',
            'Имя: Алексей',
            'Отчество: Примерович',
            'Дата выдачи: 12.05.2020',
            'Серия: 0000 Номер: 000000',
        ]
        kind, _ = classify_document(lines)
        self.assertEqual(kind, 'Паспорт')
        fields = extract_fields(lines, kind)
        self.assertEqual(fields['Фамилия'], 'Тестов')
        self.assertEqual(fields['Имя'], 'Алексей')
        self.assertEqual(fields['Серия и номер'], '0000 000000')
        self.assertEqual(fields['Дата выдачи'], '12.05.2020')

    def test_contract_classification_and_fields(self):
        lines = [
            'ДОГОВОР № ГД-014/26',
            'на оказание гостиничных услуг',
            'Дата договора: 02.11.2026',
            'Гость: Тестов Алексей Примерович',
            'Заезд: 15.11.2026',
            'Выезд: 19.11.2026',
            'Категория номера: Стандарт',
        ]
        kind, _ = classify_document(lines)
        self.assertEqual(kind, 'Гостиничный договор')
        fields = extract_fields(lines, kind)
        self.assertEqual(fields['Номер договора'], 'ГД-014/26')
        self.assertEqual(fields['Дата договора'], '02.11.2026')
        self.assertEqual(fields['Дата заезда'], '15.11.2026')
        self.assertEqual(fields['Дата выезда'], '19.11.2026')
        self.assertEqual(fields['Номер / категория'], 'Стандарт')

    def test_empty_or_unknown(self):
        self.assertEqual(classify_document([])[0], 'Не определён')
        self.assertEqual(classify_document(['Кофе молоко'])[0], 'Не определён')
        self.assertEqual(extract_fields([], 'Не определён'), {})
        self.assertIsNone(find_valid_date('31.02.2026'))

    def test_contract_with_passport_reference(self):
        # В гостиничном договоре бывает слово «паспорт»: это не должно
        # автоматически переводить документ в категорию паспорта.
        lines = ['ДОГОВОР № 14', 'на оказание гостиничных услуг',
                 'Гость: Тестов Алексей', 'Паспорт серия 0000 номер 000000',
                 'Заезд: 15.11.2026']
        self.assertEqual(classify_document(lines)[0], 'Гостиничный договор')

    def test_easyocr_result_conversion(self):
        square = [[0, 0], [10, 0], [10, 10], [0, 10]]
        result = build_result([(square, 'ПАСПОРТ', 0.8), (square, 'Фамилия: Тестов', 0.6)])
        self.assertEqual(result['document_type'], 'Паспорт')
        self.assertEqual(len(result['ocr_blocks']), 2)
        self.assertAlmostEqual(result['mean_ocr_confidence'], 0.7)
        self.assertEqual(result['fields']['Фамилия'], 'Тестов')


if __name__ == '__main__':
    unittest.main()
