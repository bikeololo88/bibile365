#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор ежедневных EPUB файлов из библии по плану чтения
"""

import os
import re
import zipfile
from pathlib import Path
from lxml import etree
from ebooklib import epub
from collections import defaultdict

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


class BibleEpubExtractor:
    def __init__(self, epub_dir):
        self.epub_dir = epub_dir
        self.book_mapping = {}
        self._build_book_mapping()

    def _build_book_mapping(self):
        """Строит маппинг книг на основе toc.ncx"""
        toc_path = os.path.join(self.epub_dir, 'OEBPS', 'toc.ncx')
        parser = etree.XMLParser(encoding='utf-8')
        tree = etree.parse(toc_path, parser)
        root = tree.getroot()

        ns = {'ncx': 'http://www.daisy.org/z3986/2005/ncx/'}
        nav_points = root.xpath('//ncx:navPoint', namespaces=ns)

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

            # Сохраняем только книги, не главы
            if not label_text.startswith('Glava ') and not label_text.startswith('Psalom '):
                self.book_mapping[label_text] = file_name

    def extract_chapter(self, book_name, chapter_num):
        """Извлекает главу из XHTML файла"""
        if book_name not in self.book_mapping:
            print(f"Книга не найдена: {book_name}")
            return None

        book_file = self.book_mapping[book_name]
        xhtml_path = os.path.join(self.epub_dir, 'OEBPS', book_file)

        if not os.path.exists(xhtml_path):
            print(f"Файл не найден: {xhtml_path}")
            return None

        try:
            parser = etree.HTMLParser(encoding='utf-8')
            tree = etree.parse(xhtml_path, parser)
            root = tree.getroot()

            # Ищем div с id="idN"
            chapter_id = f'id{chapter_num}'
            chapter_div = root.xpath(f'//div[@id="{chapter_id}"]')

            if chapter_div:
                return chapter_div[0]
            else:
                # Попробуем найти всю книгу, если глава не найдена
                print(f"Глава {chapter_num} не найдена в {book_file}, беру всю книгу")
                # Берем все div с классом section
                all_sections = root.xpath('//div[@class="section"]')
                return all_sections if all_sections else None
        except Exception as e:
            print(f"Ошибка при парсинге {xhtml_path}: {e}")
            return None


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
    """
    Парсит ссылку на главу типа 'Быт. 1', 'Мф. 1:1-17'
    """
    ref = ref.strip()
    pattern = r'^([\dА-Яа-я\s]+)\.\s*(\d+)(?::(\d+)-(\d+))?$'
    match = re.match(pattern, ref)

    if match:
        book = match.group(1).strip()
        chapter = int(match.group(2))
        verse_start = int(match.group(3)) if match.group(3) else None
        verse_end = int(match.group(4)) if match.group(4) else None
        return (book, chapter, verse_start, verse_end)

    return None


def create_daily_epub(day_name, day_data, extractor, output_dir):
    """Создает EPUB файл для одного дня"""
    book = epub.EpubBook()

    day_num = day_data['number']
    book.set_identifier(f'bible365-day-{day_num}')
    book.set_title(f'Библия 365 - {day_name}')
    book.set_language('ru')
    book.add_author('Библия')

    html_content = '''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>{day_name}</title>
<style type="text/css">
body {{ font-family: serif; margin: 1em; }}
.title {{ text-align: center; font-size: 1.5em; font-weight: bold; margin: 1em 0; }}
.section {{ margin: 2em 0; }}
.title3, .title4 {{ margin: 1em 0; }}
.title-p {{ font-weight: bold; font-size: 1.2em; text-align: center; }}
.p {{ margin: 0.5em 0; text-indent: 1.5em; line-height: 1.6; }}
.p em {{ font-weight: bold; font-style: normal; color: #666; }}
.img {{ text-align: center; margin: 1em 0; display: none; }}
</style>
</head>
<body>
<div class="title">{day_name}</div>
<div class="title" style="font-size: 1em; color: #666;">Вся Библия за год</div>
'''.format(day_name=day_name)

    # Добавляем главы
    for chapter_ref in day_data['chapters']:
        parsed = parse_chapter_reference(chapter_ref)
        if not parsed:
            continue

        book_abbr, chapter_num, verse_start, verse_end = parsed

        # Находим полное название книги
        if book_abbr not in BOOK_ABBR_TO_FULL:
            print(f"Сокращение не найдено: {book_abbr}")
            continue

        book_search = BOOK_ABBR_TO_FULL[book_abbr]

        # Ищем книгу в маппинге
        matched_book = None
        for book_name in extractor.book_mapping.keys():
            if book_search.lower() in book_name.lower():
                matched_book = book_name
                break

        if not matched_book:
            print(f"Книга не найдена: {book_search} (сокращение: {book_abbr})")
            continue

        # Извлекаем главу
        chapter_div = extractor.extract_chapter(matched_book, chapter_num)

        if chapter_div is not None:
            if isinstance(chapter_div, list):
                # Вся книга
                for div in chapter_div:
                    html_content += etree.tostring(div, encoding='unicode', method='html')
            else:
                # Одна глава
                html_content += '<div class="section">\n'
                html_content += etree.tostring(chapter_div, encoding='unicode', method='html')
                html_content += '</div>\n'

    html_content += '</body></html>'

    # Создаем EPUB главу
    c1 = epub.EpubHtml(title=day_name, file_name='content.xhtml', lang='ru')
    c1.content = html_content

    book.add_item(c1)
    book.toc = (epub.Link('content.xhtml', day_name, 'content'),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav', c1]

    output_path = os.path.join(output_dir, f'day_{day_num:03d}.epub')
    epub.write_epub(output_path, book)
    print(f"✓ Создан: {output_path}")


def main():
    days_file = 'days'
    epub_dir = 'epub_extracted'
    output_dir = 'daily_epubs'

    os.makedirs(output_dir, exist_ok=True)

    print("Инициализация экстрактора...")
    extractor = BibleEpubExtractor(epub_dir)
    print(f"Найдено книг: {len(extractor.book_mapping)}")

    print("\nПарсинг файла days...")
    days = parse_days_file(days_file)
    print(f"Найдено дней: {len(days)}")

    print("\nГенерация EPUB файлов...")
    for day_name, day_data in sorted(days.items(), key=lambda x: x[1]['number']):
        create_daily_epub(day_name, day_data, extractor, output_dir)

    print(f"\n✓ Готово! Создано {len(days)} EPUB файлов в папке {output_dir}/")


if __name__ == '__main__':
    main()
