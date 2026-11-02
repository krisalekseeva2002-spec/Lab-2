"""HotelDoc AI — локальная учебная демонстрация OCR гостиничных документов."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import numpy as np
import streamlit as st
from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

from core import build_result

BASE_DIR = Path(__file__).resolve().parent
EXAMPLES = BASE_DIR / 'examples'
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_SIDE = 2400

st.set_page_config(page_title='HotelDoc AI', page_icon='🏨', layout='wide')
st.markdown('''
<style>
.block-container {max-width: 1170px; padding-top: 2rem;}
.hero {padding: 22px 26px; border-radius: 16px; background: #10283e; color: #fafafa; margin-bottom: 20px;}
.hero h1 {font-size: 2rem; margin: 0 0 5px 0; color: #fff;}
.hero p {font-size: 1rem; margin: 0; color: #cbd9e5;}
.small-note {color: #667782; font-size: .89rem;}
</style>
''', unsafe_allow_html=True)
st.markdown('''<div class="hero"><h1>HotelDoc AI</h1>
<p>Нейросетевое распознавание паспорта и договора на оказание гостиничных услуг</p></div>''',
            unsafe_allow_html=True)


@st.cache_resource(show_spinner='Загружаем нейросетевую модель EasyOCR…')
def get_reader():
    import easyocr
    # Работает на CPU, установка GPU / CUDA не требуется.
    # Модели автоматически загружаются при первом запуске (требуется интернет).
    return easyocr.Reader(['ru', 'en'], gpu=False)


def prepare_image(data: bytes) -> Image.Image:
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError('Файл больше 10 МБ.')
    try:
        with Image.open(io.BytesIO(data)) as opened:
            if opened.width * opened.height > 18_000_000:
                raise ValueError('Слишком большое изображение (максимум 18 млн пикселей).')
            image = ImageOps.exif_transpose(opened).convert('RGB')
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError('Не удалось открыть изображение. Нужен JPG или PNG.') from exc
    image.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE), Image.Resampling.LANCZOS)
    return image


def draw_boxes(image: Image.Image, blocks: list[dict]) -> Image.Image:
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    width = max(2, image.width // 650)
    for block in blocks:
        points = [tuple(point) for point in block['box']]
        if len(points) >= 3:
            draw.line(points + [points[0]], fill='#0077bb', width=width, joint='curve')
    return annotated


with st.sidebar:
    st.subheader('О проекте')
    st.write('**EasyOCR** — нейросетевое обнаружение и чтение текста на изображении.')
    st.write('Тип документа и реквизиты определяются простыми правилами по распознанному тексту.')
    st.info('Учебный прототип. Не проверяет подлинность паспорта или юридическую силу договора.')
    st.caption('Распознавание выполняется локально. Программа не сохраняет изображения или данные в файлы и не отправляет их в облачный OCR.')

source = st.radio(
    'Выберите изображение',
    ['Учебный паспорт', 'Учебный договор', 'Загрузить своё'],
    horizontal=True,
)

if source == 'Загрузить своё':
    uploaded = st.file_uploader('Загрузите скан или фотографию', type=['png', 'jpg', 'jpeg'],
                                help='Форматы JPG, PNG. Максимум 10 МБ.')
    raw = uploaded.getvalue() if uploaded else None
elif source == 'Учебный паспорт':
    raw = (EXAMPLES / 'passport_demo.png').read_bytes()
else:
    raw = (EXAMPLES / 'contract_demo.png').read_bytes()

if not raw:
    st.info('Загрузите JPG или PNG для распознавания.')
    st.stop()

try:
    image = prepare_image(raw)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

identity = hashlib.sha256(raw).hexdigest()
if st.session_state.get('source_identity') != identity:
    st.session_state.pop('analysis', None)
    st.session_state['source_identity'] = identity

left, right = st.columns([1, 1], gap='large')
with left:
    st.subheader('Изображение')
    st.image(image, use_container_width=True)
    st.caption(f'Размер после подготовки: {image.width} × {image.height} пикселей')
with right:
    st.subheader('Анализ')
    st.write('Модель выделяет текстовые области, распознаёт русский и английский текст, '
             'затем программа определяет тип документа и извлекает реквизиты.')
    run = st.button('Распознать документ', type='primary', use_container_width=True)
    if run:
        try:
            with st.spinner('Распознавание изображения…'):
                reader = get_reader()
                raw_ocr = reader.readtext(np.array(image), detail=1, paragraph=False)
                st.session_state['analysis'] = build_result(raw_ocr)
        except Exception as exc:
            # Не записываем персональные данные в логи / crash report.
            st.error('Не удалось выполнить OCR. Проверьте установку зависимостей и доступность моделей EasyOCR.')
            with st.expander('Техническая ошибка'):
                st.code(f'{type(exc).__name__}: {exc}')

result = st.session_state.get('analysis')
if not result:
    st.info('Нажмите «Распознать документ», чтобы увидеть результат.')
    st.stop()

st.divider()
st.subheader('Результаты распознавания')
a, b, c = st.columns(3)
a.metric('Тип документа', result['document_type'])
b.metric('Найдено текстовых блоков', len(result['ocr_blocks']))
c.metric('Средняя оценка OCR', f"{result['mean_ocr_confidence']:.0%}" if result['mean_ocr_confidence'] is not None else '—')
st.caption('Оценка OCR — усреднение оценок для отдельных текстовых блоков, '
           'а не вероятность правильного определения типа документа.')

col1, col2 = st.columns(2, gap='large')
with col1:
    st.markdown('**Найденные реквизиты**')
    if result['fields']:
        for key, value in result['fields'].items():
            st.text(f'{key}: {value}')
    else:
        st.warning('Не удалось надёжно выделить реквизиты. Проверьте полный текст ниже.')
    with st.expander('Как определён тип документа'):
        st.write('Классификация выполнена по ключевым словам в результате OCR, не отдельной нейросетью.')
        st.json(result['classification_scores'])
with col2:
    st.markdown('**Области, найденные нейросетью**')
    st.image(draw_boxes(image, result['ocr_blocks']), use_container_width=True)

with st.expander('Полный распознанный текст', expanded=True):
    st.text_area('Результат OCR', result['text'] or 'Текст не обнаружен', height=250)

json_bytes = json.dumps(result, ensure_ascii=False, indent=2).encode('utf-8')
st.download_button('Скачать результат (JSON)', data=json_bytes,
                   file_name='hotel_doc_result.json', mime='application/json')
st.warning('Если используете реальные персональные данные гостей, требуется законное основание '
           'для обработки, контроль доступа и ручная проверка полей. Для лабораторной '
           'рекомендуются только учебные примеры.')
