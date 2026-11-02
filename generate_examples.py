"""Генерация двух полностью вымышленных образцов для лабораторной работы."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent / 'examples'
OUT.mkdir(exist_ok=True)
FONT_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype(BOLD_PATH if bold else FONT_PATH, size)
    except OSError:
        # Windows: fonts are included with the OS, PIL searches the font name.
        return ImageFont.truetype('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf', size)


def line(draw: ImageDraw.ImageDraw, text: str, x: int, y: int, size: int = 33,
         color: str = '#293a50', bold: bool = False):
    draw.text((x, y), text, font=font(size, bold), fill=color)


def demo_passport():
    img = Image.new('RGB', (1400, 1040), '#f7f6f1')
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((65, 65, 1335, 975), radius=20,
                           fill='#ffffff', outline='#b5c5d3', width=5)
    draw.rectangle((65, 65, 1335, 220), fill='#e5edf4')
    line(draw, 'ОБРАЗЕЦ ДЛЯ УЧЕБНОЙ РАБОТЫ', 112, 98, 37, '#235780', True)
    line(draw, 'ПАСПОРТ — УЧЕБНЫЙ МАКЕТ', 112, 162, 29, '#48687e')
    line(draw, 'РОССИЙСКАЯ ФЕДЕРАЦИЯ (МАКЕТ)', 112, 270, 36, bold=True)
    draw.line((110, 340, 1288, 340), fill='#d8e0e8', width=3)
    rows = [
        'Фамилия: Тестов',
        'Имя: Алексей',
        'Отчество: Примерович',
        'Дата рождения: 01.01.2000',
        'Место рождения: Учебный город',
        'Дата выдачи: 12.05.2020',
        'Код подразделения: 000-000',
        'Серия: 0000 Номер: 000000',
    ]
    for idx, item in enumerate(rows):
        line(draw, item, 118, 375 + idx * 62, 33)
    draw.rectangle((112, 902, 1280, 950), fill='#fff0f0')
    line(draw, 'НЕ ЯВЛЯЕТСЯ ДОКУМЕНТОМ', 142, 907, 28, '#9e3434', True)
    img.save(OUT / 'passport_demo.png')


def demo_contract():
    img = Image.new('RGB', (1400, 1660), '#f1f4f6')
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((65, 65, 1335, 1580), radius=18,
                           fill='#ffffff', outline='#bdcbd6', width=5)
    draw.rectangle((65, 65, 1335, 225), fill='#e9f0f6')
    line(draw, 'HOTEL LAB — УЧЕБНАЯ ГОСТИНИЦА', 116, 107, 39, '#255476', True)
    line(draw, 'Вымышленные реквизиты. Документ создан для демонстрации OCR.',
         116, 177, 23, '#506a7f')
    line(draw, 'ДОГОВОР № ГД-014/26', 116, 285, 43, bold=True)
    line(draw, 'на оказание гостиничных услуг', 116, 358, 31)
    draw.line((110, 425, 1290, 425), fill='#d4dfe8', width=3)
    rows = [
        ('Дата договора: 02.11.2026', 477),
        ('Гость: Тестов Алексей Примерович', 551),
        ('Заезд: 15.11.2026', 625),
        ('Выезд: 19.11.2026', 699),
        ('Категория номера: Стандарт', 773),
        ('Стоимость проживания: 16 000 руб.', 847),
    ]
    for text, y in rows:
        line(draw, text, 116, y, 33)
    line(draw, '1. Исполнитель предоставляет услуги размещения', 116, 1030, 28)
    line(draw, 'в гостинице, а заказчик оплачивает проживание.', 116, 1080, 28)
    line(draw, '2. Стороны согласовали срок пребывания.', 116, 1170, 28)
    draw.line((110, 1320, 1290, 1320), fill='#d4dfe8', width=3)
    line(draw, 'Подпись гостя: ___________', 116, 1360, 26)
    line(draw, 'Подпись исполнителя: ___________', 116, 1420, 26)
    draw.rectangle((110, 1495, 1290, 1550), fill='#fff0f0')
    line(draw, 'УЧЕБНЫЙ ПРИМЕР — НЕ ДЕЙСТВУЕТ', 131, 1504, 28, '#9e3434', True)
    img.save(OUT / 'contract_demo.png')


if __name__ == '__main__':
    demo_passport()
    demo_contract()
    print('Created example images in', OUT)
