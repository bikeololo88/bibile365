#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор ежедневных EPUB файлов из библии по плану чтения
"""

import os
import re
from lxml import etree
from ebooklib import epub

# Маппинг сокращений книг к их полным названиям (транслитерация)
BOOK_ABBR_TO_FULL = {
    # Ветхий Завет
    'Быт': 'Bytie',
    'Исх': 'Ishod',
    'Лев': 'Levit',
    'Чис': 'Chisla',
    'Втор': 'Vtorozakonie',
    'Нав': 'Iisusa Navina',
    'Суд': 'Sudej',
    'Руф': 'Rufi',
    '1 Цар': 'Pervaya kniga Tsarstv',
    '2 Цар': 'Vtoraya kniga Tsarstv',
    '3 Цар': "Tret'ya kniga Tsarstv",
    '4 Цар': 'Chetvyortaya kniga Tsarstv',
    '1 Пар': 'Pervaya kniga Paralipomenon',
    '2 Пар': 'Vtoraya kniga Paralipomenon',
    '1 Езд': 'Pervaya kniga Ezdry',
    '2 Езд': 'Vtoraya kniga Ezdry',
    'Неем': 'Neemii',
    'Тов': 'Tovita',
    'Иудиф': 'Iudifi',
    'Есф': 'Esfiri',
    'Иов': 'Iova',
    'Пс': "Psaltir'",
    'Притч': 'Pritchi Solomona',
    'Еккл': 'Ekkleziast',
    'Песн': "Pesn' pesnej Solomona",
    'Прем': 'premudrosti Solomona',
    'Сир': 'premudrosti Iisusa',
    'Ис': 'Isaii',
    'Иер': 'Ieremii',
    'Плач': 'Plach Ieremii',
    'Посл': 'Poslanie Ieremii',
    'Вар': 'Varuha',
    'Иез': 'Iezekiilya',
    'Дан': 'Daniila',
    'Ос': 'Osii',
    'Иоил': 'Ioilya',
    'Ам': 'Amosa',
    'Авд': 'Avdiya',
    'Ион': 'Iony',
    'Мих': 'Miheya',
    'Наум': 'Nauma',
    'Авв': 'Avvakuma',
    'Соф': 'Sofonii',
    'Агг': 'Aggeya',
    'Зах': 'Zaharii',
    'Мал': 'Malahii',
    '1 Мак': 'Pervaya kniga Makkavejskaya',
    '2 Мак': 'Vtoraya kniga Makkavejskaya',
    '3 Мак': "Tret'ya kniga Makkavejskaya",
    '3 Езд': "Tret'ya kniga Ezdry",

    # Новый Завет
    'Мф': 'Matfeya',
    'Мк': 'Marka',
    'Лк': 'Luki',
    'Ин': 'Ioanna',
    'Деян': 'Deyaniya',
    'Иак': 'Iakova',
    '1 Пет': 'Pervoe sobornoe poslanie svyatogo apostola Petra',
    '2 Пет': 'Vtoroe sobornoe poslanie svyatogo apostola Petra',
    '1 Ин': 'Pervoe sobornoe poslanie svyatogo apostola Ioanna',
    '2 Ин': 'Vtoroe sobornoe poslanie svyatogo apostola Ioanna',
    '3 Ин': "Tret'e sobornoe poslanie svyatogo apostola Ioanna",
    'Иуд': 'Iudy',
    'Рим': 'Rimlyanam',
    '1 Кор': 'Pervoe poslanie k Korinfyanam',
    '2 Кор': 'Vtoroe poslanie k Korinfyanam',
    'Гал': 'Galatam',
    'Еф': 'Efesyanam',
    'Флп': 'Filippijtsam',
    'Кол': 'Kolossyanam',
    '1 Фес': 'Pervoe poslanie k Fessalonikijtsam',
    '2 Фес': 'Vtoroe poslanie k Fessalonikijtsam',
    '1 Тим': 'Pervoe poslanie k Timofeyu',
    '2 Тим': 'Vtoroe poslanie k Timofeyu',
    'Тит': 'Titu',
    'Флм': 'Filimonu',
    'Евр': 'Evreyam',
    'Откр': 'Otkrovenie',
}

# Словарь русских названий книг для отображения
BOOK_ABBR_TO_RU = {
    'Быт': 'Бытие',
    'Исх': 'Исход',
    'Лев': 'Левит',
    'Чис': 'Числа',
    'Втор': 'Второзаконие',
    'Нав': 'Иисус Навин',
    'Суд': 'Судей',
    'Руф': 'Руфь',
    '1 Цар': '1 Царств',
    '2 Цар': '2 Царств',
    '3 Цар': '3 Царств',
    '4 Цар': '4 Царств',
    '1 Пар': '1 Паралипоменон',
    '2 Пар': '2 Паралипоменон',
    '1 Езд': '1 Ездры',
    '2 Езд': '2 Ездры',
    'Неем': 'Неемия',
    'Тов': 'Товит',
    'Иудиф': 'Иудифь',
    'Есф': 'Есфирь',
    'Иов': 'Иов',
    'Пс': 'Псалтирь',
    'Притч': 'Притчи',
    'Еккл': 'Екклесиаст',
    'Песн': 'Песнь Песней',
    'Прем': 'Премудрость Соломона',
    'Сир': 'Премудрость Сираха',
    'Ис': 'Исаия',
    'Иер': 'Иеремия',
    'Плач': 'Плач Иеремии',
    'Посл': 'Послание Иеремии',
    'Вар': 'Варух',
    'Иез': 'Иезекииль',
    'Дан': 'Даниил',
    'Ос': 'Осия',
    'Иоил': 'Иоиль',
    'Ам': 'Амос',
    'Авд': 'Авдий',
    'Ион': 'Иона',
    'Мих': 'Михей',
    'Наум': 'Наум',
    'Авв': 'Аввакум',
    'Соф': 'Софония',
    'Агг': 'Аггей',
    'Зах': 'Захария',
    'Мал': 'Малахия',
    '1 Мак': '1 Маккавейская',
    '2 Мак': '2 Маккавейская',
    '3 Мак': '3 Маккавейская',
    '3 Езд': '3 Ездры',
    'Мф': 'Евангелие от Матфея',
    'Мк': 'Евангелие от Марка',
    'Лк': 'Евангелие от Луки',
    'Ин': 'Евангелие от Иоанна',
    'Деян': 'Деяния',
    'Иак': 'Иакова',
    '1 Пет': '1 Петра',
    '2 Пет': '2 Петра',
    '1 Ин': '1 Иоанна',
    '2 Ин': '2 Иоанна',
    '3 Ин': '3 Иоанна',
    'Иуд': 'Иуда',
    'Рим': 'Римлянам',
    '1 Кор': '1 Коринфянам',
    '2 Кор': '2 Коринфянам',
    'Гал': 'Галатам',
    'Еф': 'Ефесянам',
    'Флп': 'Филиппийцам',
    'Кол': 'Колоссянам',
    '1 Фес': '1 Фессалоникийцам',
    '2 Фес': '2 Фессалоникийцам',
    '1 Тим': '1 Тимофею',
    '2 Тим': '2 Тимофею',
    'Тит': 'Титу',
    'Флм': 'Филимону',
    'Евр': 'Евреям',
    'Откр': 'Откровение',
}

class BibleEpubExtractor:
    def __init__(self, epub_dir):
        self.epub_dir = epub_dir
        self.book_mapping = {}
        self._build_book_mapping()

    def _build_book_mapping(self):
        """Строит маппинг книг на основе toc.ncx, собирая все файлы для каждой книги"""
        toc_path = os.path.join(self.epub_dir, 'OEBPS', 'toc.ncx')
        parser = etree.XMLParser(encoding='utf-8')
        tree = etree.parse(toc_path, parser)
        root = tree.getroot()

        ns = {'ncx': 'http://www.daisy.org/z3986/2005/ncx/'}
        nav_points = root.xpath('//ncx:navPoint', namespaces=ns)

        current_book = None

        for nav_point in nav_points:
            label = nav_point.xpath('.//ncx:text', namespaces=ns)
            if not label:
                continue

            label_text = label[0].text
            content = nav_point.xpath('.//ncx:content', namespaces=ns)
            if not content:
                continue

            src = content[0].get('src')
            file_name = src.split('#')[0]

            # Сохраняем названия книг и привязываем к ним все файлы глав
            if not label_text.startswith('Glava ') and not label_text.startswith('Psalom '):
                current_book = label_text
                if current_book not in self.book_mapping:
                    self.book_mapping[current_book] = []

            # Добавляем файл к текущей книге, если его там еще нет
            if current_book and file_name not in self.book_mapping[current_book]:
                self.book_mapping[current_book].append(file_name)

    def extract_chapter(self, book_name, chapter_num):
        """Извлекает главу, находя ее по тексту 'Глава N' или 'Псалом N' и забирая родительский блок"""
        if book_name not in self.book_mapping:
            return None, f"Книга не найдена: {book_name}"

        book_files = self.book_mapping[book_name]
        search_text = f"Глава {chapter_num}"
        search_psalom = f"Псалом {chapter_num}"

        # Проходимся по всем файлам этой книги
        for book_file in book_files:
            xhtml_path = os.path.join(self.epub_dir, 'OEBPS', book_file)

            if not os.path.exists(xhtml_path):
                continue

            try:
                parser = etree.HTMLParser(encoding='utf-8')
                tree = etree.parse(xhtml_path, parser)
                root = tree.getroot()

                # Ищем <p> (или любой другой тег), внутри которого написан текст "Глава 20" или "Псалом 20"
                nodes = root.xpath(f'//*[contains(text(), "{search_text}") or contains(text(), "{search_psalom}")]')
                
                if nodes:
                    node = nodes[0]
                    # Нам нужно подняться вверх по дереву и найти главный <div class="section">,
                    # внутри которого лежит эта глава.
                    parent_sections = node.xpath('ancestor::div[contains(@class, "section")]')
                    
                    if parent_sections:
                        # Возвращаем найденную секцию с главой
                        return parent_sections[0], None
                    
                    # Если вдруг class="section" нет, берем ближайший родительский div
                    parent_divs = node.xpath('ancestor::div[1]')
                    if parent_divs:
                         return parent_divs[0], None

            except Exception as e:
                pass # Игнорируем ошибки парсинга конкретного файла

        return None, f"Глава {chapter_num} не найдена в файлах книги ({len(book_files)} шт.)"


def parse_days_file(filepath):
    """Парсит файл days и возвращает словарь с планом чтения"""
    days = {}
    current_day = None

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            if line.startswith('День '):
                current_day = line
                days[current_day] = {'number': None, 'chapters': []}
            elif current_day and line.isdigit():
                days[current_day]['number'] = int(line)
            elif current_day:
                days[current_day]['chapters'].append(line)

    return days


def parse_chapter_reference(ref):
    """Извлекает только название книги и первое число (главу), игнорируя диапазоны и стихи"""
    ref = ref.strip()
    # Ищет книгу (буквы/цифры до точки) и первую группу цифр после неё
    pattern = r'^([\dА-Яа-я\s]+)\.\s*(\d+)'
    match = re.search(pattern, ref)

    if match:
        book = match.group(1).strip()
        chapter_num = int(match.group(2))
        return (book, chapter_num)

    return None


def create_daily_epub(day_name, day_data, extractor, output_dir):
    """Создает EPUB файл для одного дня"""
    book = epub.EpubBook()

    day_num = day_data['number']
    book.set_identifier(f'bible365-day-{day_num}')
    book.set_title(f'Библия 365 - {day_name}')
    book.set_language('ru')
    book.add_author('Библия')

    html_parts = []
    html_parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    html_parts.append('<html xmlns="http://www.w3.org/1999/xhtml">')
    html_parts.append('<head>')
    html_parts.append(f'<title>{day_name}</title>')
    html_parts.append('<style type="text/css">')
    html_parts.append('body { font-family: serif; margin: 1em; }')
    html_parts.append('.day-title { text-align: center; font-size: 1.8em; font-weight: bold; margin: 1em 0; }')
    html_parts.append('.subtitle { text-align: center; font-size: 1em; color: #666; margin-bottom: 2em; }')
    html_parts.append('.book-title { font-size: 1.3em; font-weight: bold; margin-top: 2em; margin-bottom: 0.5em; color: #333; }')
    html_parts.append('.chapter-title { font-size: 1.1em; font-weight: bold; margin-top: 1em; margin-bottom: 0.5em; }')
    html_parts.append('.verse { margin: 0.5em 0; text-indent: 1.5em; line-height: 1.6; }')
    html_parts.append('.verse-num { font-weight: bold; font-style: normal; color: #666; }')
    html_parts.append('</style>')
    html_parts.append('</head>')
    html_parts.append('<body>')
    html_parts.append(f'<div class="day-title">{day_name}</div>')
    html_parts.append('<div class="subtitle">Вся Библия за год</div>')

    # Добавляем главы
    for chapter_ref in day_data['chapters']:
        parsed = parse_chapter_reference(chapter_ref)
        if not parsed:
            print(f"  ! Не удалось распарсить ссылку: {chapter_ref}")
            continue

        book_abbr, chapter_num = parsed

        # Находим полное название книги
        if book_abbr not in BOOK_ABBR_TO_FULL:
            print(f"  ! Сокращение не найдено: {book_abbr}")
            continue

        book_search = BOOK_ABBR_TO_FULL[book_abbr]
        russian_name = BOOK_ABBR_TO_RU.get(book_abbr, book_abbr)

        # Ищем книгу в маппинге
        matched_book = None
        for book_name in extractor.book_mapping.keys():
            if book_search.lower() in book_name.lower():
                matched_book = book_name
                break

        if not matched_book:
            print(f"  ! Книга не найдена: {book_search} (сокращение: {book_abbr})")
            continue

        # Извлекаем ровно одну главу
        chapter_div, error = extractor.extract_chapter(matched_book, chapter_num)

        if error:
            print(f"  ! {error}")

        if chapter_div is not None:
            # Добавляем заголовок книги и главы
            html_parts.append(f'<div class="book-title">{russian_name}. Глава {chapter_num}</div>')

            # Извлекаем содержимое главы
            chapter_html = etree.tostring(chapter_div, encoding='unicode', method='html')
            html_parts.append(chapter_html)

    html_parts.append('</body>')
    html_parts.append('</html>')

    html_content = '\n'.join(html_parts)

    # Проверяем, что контент не пустой
    if len(html_content) < 500:  # Минимальный размер HTML с главами
        print(f"  ! Контент слишком короткий, пропускаем день {day_num}")
        return False

    # Создаем EPUB главу
    c1 = epub.EpubHtml(title=day_name, file_name='content.xhtml', lang='ru')
    c1.set_content(html_content.encode('utf-8'))

    book.add_item(c1)
    book.toc = (c1,)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav', c1]

    output_path = os.path.join(output_dir, f'day_{day_num:03d}.epub')
    try:
        epub.write_epub(output_path, book, {'epub3_pages': False})
        return True
    except Exception as e:
        print(f"  ! Ошибка сохранения: {e}")
        return False


def main():
    days_file = 'days'
    epub_dir = '.'  # Папка с распакованной книгой (точка = текущая папка)
    output_dir = 'daily_epubs'

    os.makedirs(output_dir, exist_ok=True)

    print("Инициализация экстрактора...")
    extractor = BibleEpubExtractor(epub_dir)
    print(f"Найдено книг: {len(extractor.book_mapping)}")

    print("\nПарсинг файла days...")
    days = parse_days_file(days_file)
    print(f"Найдено дней: {len(days)}")

    print("\nГенерация EPUB файлов...")
    success_count = 0
    for day_name, day_data in sorted(days.items(), key=lambda x: x[1]['number']):
        print(f"\n{day_name}...")
        if create_daily_epub(day_name, day_data, extractor, output_dir):
            print(f"  ✓ Создан день {day_data['number']}")
            success_count += 1

    print(f"\n{'='*50}")
    print(f"✓ Готово! Создано {success_count} из {len(days)} EPUB файлов")
    print(f"Результаты в папке: {output_dir}/")


if __name__ == '__main__':
    main()