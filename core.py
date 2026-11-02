"""Логика демонстрационного распознавателя гостиничных документов.

Распознавание текста делает нейросетевая модель EasyOCR (см. app.py).
Классификация документа и извлечение полей — объяснимые правила.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any


PASSPORT_TERMS = {
    'паспорт': 4,
    'российская федерация': 3,
    'дата выдачи': 2,
    'код подразделения': 2,
    'место рождения': 2,
    'фамилия': 1,
    'отчество': 1,
}
CONTRACT_TERMS = {
    'договор': 5,
    'гостиничн': 3,
    'заезд': 2,
    'выезд': 2,
    'проживани': 2,
    'заказчик': 2,
    'исполнитель': 2,
    'оказани': 1,
    'стороны': 1,
}
DATE_PATTERN = r'(?:0?[1-9]|[12]\d|3[01])\.(?:0?[1-9]|1[0-2])\.(?:19|20)\d{2}'


def normalize(text: str) -> str:
    """Нормализация, не меняющая содержимое исходного текста OCR."""
    return re.sub(r'\s+', ' ', text.casefold().replace('ё', 'е')).strip()


def classify_document(lines: list[str]) -> tuple[str, dict[str, int]]:
    """Возвращает тип и баллы правил, а НЕ вероятности нейросети."""
    text = normalize(' '.join(lines))
    scores = {
        'Паспорт': sum(weight for term, weight in PASSPORT_TERMS.items() if term in text),
        'Гостиничный договор': sum(weight for term, weight in CONTRACT_TERMS.items() if term in text),
    }
    top = max(scores, key=scores.get)
    if scores[top] < 4 or scores[top] == scores['Паспорт' if top == 'Гостиничный договор' else 'Гостиничный договор']:
        return 'Не определён', scores
    return top, scores


def find_valid_date(text: str) -> str | None:
    for match in re.finditer(r'(?<!\d)' + DATE_PATTERN + r'(?!\d)', text):
        candidate = match.group(0)
        try:
            datetime.strptime(candidate, '%d.%m.%Y')
            return candidate
        except ValueError:
            continue
    return None


def _find_labeled_value(lines: list[str], labels: list[str], value_pattern: str = r'[^,;]{2,70}') -> str | None:
    """Для демонстрационных макетов с надписью «Поле: значение»."""
    label_part = '|'.join(re.escape(label) for label in labels)
    regex = re.compile(rf'^\s*(?:{label_part})\s*[:：-]\s*({value_pattern})\s*$', re.IGNORECASE)
    for idx, line in enumerate(lines):
        match = regex.search(line.strip())
        if match:
            return match.group(1).strip()
        # Если OCR разнёс подпись и значение по разным блокам.
        if re.fullmatch(rf'\s*(?:{label_part})\s*[:：]?\s*', line, re.IGNORECASE) and idx + 1 < len(lines):
            following = lines[idx + 1].strip()
            if 2 <= len(following) <= 70:
                return following
    return None


def _labeled_date(lines: list[str], labels: list[str]) -> str | None:
    prefix = '|'.join(re.escape(x) for x in labels)
    for idx, line in enumerate(lines):
        if re.search(rf'\b(?:{prefix})\b', line, flags=re.IGNORECASE):
            found = find_valid_date(line)
            if not found and idx + 1 < len(lines):
                found = find_valid_date(lines[idx + 1])
            if found:
                return found
    return None


def extract_fields(lines: list[str], doc_type: str) -> dict[str, str]:
    text = '\n'.join(lines)
    fields: dict[str, str] = {}
    if doc_type == 'Паспорт':
        # В реальном документе серия и номер могут быть нанесены иначе.
        found = re.search(r'\b[Сс]ери[яи]\s*[:№-]?\s*(\d{2}\s?\d{2})\s*[,;]?\s*(?:[Нн]омер|№|N)\s*[:№-]?\s*(\d{6})\b',
                          normalize(text), re.IGNORECASE)
        if not found:
            found = re.search(r'\b(\d{2}\s?\d{2})\s+(\d{6})\b', text)
        if found:
            fields['Серия и номер'] = f'{found.group(1)} {found.group(2)}'
        for label in ('Фамилия', 'Имя', 'Отчество'):
            value = _find_labeled_value(lines, [label], r'[А-ЯЁа-яёA-Za-z\- ]{2,50}')
            if value:
                fields[label] = value
        issued = _labeled_date(lines, ['Дата выдачи', 'Выдан'])
        if issued:
            fields['Дата выдачи'] = issued
        birth = _labeled_date(lines, ['Дата рождения'])
        if birth:
            fields['Дата рождения'] = birth
    elif doc_type == 'Гостиничный договор':
        match = re.search(r'\bдоговор\s*(?:№|N|No\.?|#)\s*([А-ЯЁа-яёA-Za-z0-9_/-]+)',
                          text, re.IGNORECASE)
        if match:
            fields['Номер договора'] = match.group(1)
        date = _labeled_date(lines, ['Дата договора', 'Дата заключения'])
        if not date:
            date = find_valid_date(text)
        if date:
            fields['Дата договора'] = date
        for label, names in [('Дата заезда', ['Заезд', 'Дата заезда']),
                             ('Дата выезда', ['Выезд', 'Дата выезда'])]:
            value = _labeled_date(lines, names)
            if value:
                fields[label] = value
        guest = _find_labeled_value(lines, ['Гость', 'Заказчик'], r'[А-ЯЁа-яёA-Za-z\- ]{3,70}')
        if guest:
            fields['Гость'] = guest
        room = _find_labeled_value(lines, ['Номер комнаты', 'Категория номера', 'Номер'], r'[А-ЯЁа-яёA-Za-z0-9\- ]{1,45}')
        if room:
            fields['Номер / категория'] = room
    return fields


def build_result(ocr_results: list[tuple[Any, str, float]]) -> dict[str, Any]:
    """Принимает обычный вывод EasyOCR readtext(detail=1)."""
    blocks = []
    for box, text, confidence in ocr_results:
        if not text or not text.strip():
            continue
        blocks.append({
            'box': [[int(round(float(x))), int(round(float(y)))] for x, y in box],
            'text': str(text).strip(),
            'confidence': round(float(confidence), 4),
        })
    lines = [block['text'] for block in blocks]
    doc_type, scores = classify_document(lines)
    return {
        'document_type': doc_type,
        'classification_method': 'Правила по тексту, полученному нейросетью EasyOCR',
        'classification_scores': scores,
        'fields': extract_fields(lines, doc_type),
        'text': '\n'.join(lines),
        'ocr_blocks': blocks,
        'mean_ocr_confidence': round(sum(b['confidence'] for b in blocks) / len(blocks), 3) if blocks else None,
    }
