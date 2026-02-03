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

# Маппинг сокращений книг к их полным названиям и файлам
BOOK_MAPPING = {
    # Ветхий Завет
    'Быт': ('Бытие', 'ch3.xhtml'),
    'Исх': ('Исход', 'ch6.xhtml'),
    'Лев': ('Левит', 'ch10.xhtml'),
    'Чис': ('Числа', 'ch14.xhtml'),
    'Втор': ('Второзаконие', 'ch20.xhtml'),
    'Нав': ('Иисус Навин', 'ch28.xhtml'),
    'Суд': ('Книга Судей', 'ch33.xhtml'),
    'Руф': ('Руфь', 'ch40.xhtml'),
    '1 Цар': ('1 Царств', 'ch42.xhtml'),
    '2 Цар': ('2 Царств', 'ch51.xhtml'),
    '3 Цар': ('3 Царств', 'ch60.xhtml'),
    '4 Цар': ('4 Царств', 'ch69.xhtml'),
    '1 Пар': ('1 Паралипоменон', 'ch78.xhtml'),
    '2 Пар': ('2 Паралипоменон', 'ch88.xhtml'),
    '1 Езд': ('1 Ездры', 'ch99.xhtml'),
    '2 Езд': ('2 Ездры', 'ch109.xhtml'),
    'Неем': ('Неемия', 'ch125.xhtml'),
    'Тов': ('Товит', 'ch133.xhtml'),
    'Иудиф': ('Иудифь', 'ch141.xhtml'),
    'Есф': ('Есфирь', 'ch108.xhtml'),
    'Иов': ('Иов', 'ch46.xhtml'),
    'Пс': ('Псалтирь', 'ch87.xhtml'),
    'Притч': ('Притчи', 'ch140.xhtml'),
    'Еккл': ('Екклесиаст', 'ch129.xhtml'),
    'Песн': ('Песнь Песней', 'ch139.xhtml'),
    'Прем': ('Премудрость Соломона', 'ch123.xhtml'),
    'Сир': ('Премудрость Иисуса сына Сирахова', 'ch124.xhtml'),
    'Ис': ('Исаия', 'ch93.xhtml'),
    'Иер': ('Иеремия', 'ch101.xhtml'),
    'Плач': ('Плач Иеремии', 'ch102.xhtml'),
    'Посл': ('Послание Иеремии', 'ch103.xhtml'),
    'Вар': ('Варух', 'ch104.xhtml'),
    'Иез': ('Иезекииль', 'ch105.xhtml'),
    'Дан': ('Даниил', 'ch115.xhtml'),
    'Ос': ('Осия', 'ch126.xhtml'),
    'Иоил': ('Иоиль', 'ch127.xhtml'),
    'Ам': ('Амос', 'ch128.xhtml'),
    'Авд': ('Авдий', 'ch130.xhtml'),
    'Ион': ('Иона', 'ch131.xhtml'),
    'Мих': ('Михей', 'ch132.xhtml'),
    'Наум': ('Наум', 'ch134.xhtml'),
    'Авв': ('Аввакум', 'ch135.xhtml'),
    'Соф': ('Софония', 'ch136.xhtml'),
    'Агг': ('Аггей', 'ch137.xhtml'),
    'Зах': ('Захария', 'ch138.xhtml'),
    'Мал': ('Малахия', 'ch141.xhtml'),
    '1 Мак': ('1 Маккавейская', 'ch106.xhtml'),
    '2 Мак': ('2 Маккавейская', 'ch107.xhtml'),
    '3 Мак': ('3 Маккавейская', 'ch110.xhtml'),
    '3 Езд': ('3 Ездры', 'ch111.xhtml'),

    # Новый Завет
    'Мф': ('Евангелие от Матфея', 'ch3.xhtml'),
    'Мк': ('Евангелие от Марка', 'ch11.xhtml'),
    'Лк': ('Евангелие от Луки', 'ch16.xhtml'),
    'Ин': ('Евангелие от Иоанна', 'ch25.xhtml'),
    'Деян': ('Деяния', 'ch34.xhtml'),
    'Иак': ('Иакова', 'ch71.xhtml'),
    '1 Пет': ('1 Петра', 'ch72.xhtml'),
    '2 Пет': ('2 Петра', 'ch73.xhtml'),
    '1 Ин': ('1 Иоанна', 'ch74.xhtml'),
    '2 Ин': ('2 Иоанна', 'ch75.xhtml'),
    '3 Ин': ('3 Иоанна', 'ch76.xhtml'),
    'Иуд': ('Иуда', 'ch77.xhtml'),
    'Рим': ('Римлянам', 'ch53.xhtml'),
    '1 Кор': ('1 Коринфянам', 'ch54.xhtml'),
    '2 Кор': ('2 Коринфянам', 'ch55.xhtml'),
    'Гал': ('Галатам', 'ch56.xhtml'),
    'Еф': ('Ефесянам', 'ch57.xhtml'),
    'Флп': ('Филиппийцам', 'ch58.xhtml'),
    'Кол': ('Колоссянам', 'ch59.xhtml'),
    '1 Фес': ('1 Фессалоникийцам', 'ch61.xhtml'),
    '2 Фес': ('2 Фессалоникийцам', 'ch62.xhtml'),
    '1 Тим': ('1 Тимофею', 'ch63.xhtml'),
    '2 Тим': ('2 Тимофею', 'ch64.xhtml'),
    'Тит': ('Титу', 'ch65.xhtml'),
    'Флм': ('Филимону', 'ch66.xhtml'),
    'Евр': ('Евреям', 'ch67.xhtml'),
    'Откр': ('Откровение', 'ch70.xhtml'),
}


def parse_days_file(filepath):
    """Парсит файл days и возвращает словарь с планом чтения"""
    days = {}
    current_day = None

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Проверяем, начинается ли строка с "День"
            if line.startswith('День '):
                current_day = line
                days[current_day] = {'number': None, 'chapters': []}
            elif current_day and line.isdigit():
                # Это номер дня
                days[current_day]['number'] = int(line)
            elif current_day:
                # Это ссылка на главу
                days[current_day]['chapters'].append(line)

    return days


def parse_chapter_reference(ref):
    """
    Парсит ссылку на главу типа 'Быт. 1', 'Мф. 1:1-17', '2 Ин. 1'
    Возвращает (книга, глава, стихи_начало, стихи_конец) или None
    """
    # Убираем точку после сокращения книги
    ref = ref.strip()

    # Паттерн для парсинга: "Книга. Глава" или "Книга. Глава:Стихи"
    # Поддержка формата "1 Цар. 1" и "Быт. 1:1-17"
    pattern = r'^([\dА-Яа-я\s]+)\.\s*(\d+)(?::(\d+)-(\d+))?$'
    match = re.match(pattern, ref)

    if match:
        book = match.group(1).strip()
        chapter = int(match.group(2))
        verse_start = int(match.group(3)) if match.group(3) else None
        verse_end = int(match.group(4)) if match.group(4) else None
        return (book, chapter, verse_start, verse_end)

    return None


def extract_chapter_from_xhtml(epub_dir, book_file, chapter_num):
    """Извлекает главу из XHTML файла"""
    xhtml_path = os.path.join(epub_dir, 'OEBPS', book_file)

    if not os.path.exists(xhtml_path):
        print(f"Файл не найден: {xhtml_path}")
        return None

    try:
        parser = etree.HTMLParser(encoding='utf-8')
        tree = etree.parse(xhtml_path, parser)
        root = tree.getroot()

        # Ищем div с id="idN", где N - номер главы
        chapter_id = f'id{chapter_num}'
        chapter_div = root.xpath(f'//div[@id="{chapter_id}"]')

        if chapter_div:
            return chapter_div[0]
        else:
            print(f"Глава {chapter_num} не найдена в {book_file}")
            return None
    except Exception as e:
        print(f"Ошибка при парсинге {xhtml_path}: {e}")
        return None


def create_daily_epub(day_name, day_data, epub_dir, output_dir):
    """Создает EPUB файл для одного дня"""
    book = epub.EpubBook()

    # Метаданные
    day_num = day_data['number']
    book.set_identifier(f'bible365-day-{day_num}')
    book.set_title(f'Библия 365 - {day_name}')
    book.set_language('ru')
    book.add_author('Библия')

    # Создаем HTML контент для дня
    html_content = '''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>{day_name}</title>
<style type="text/css">
body {{ font-family: serif; }}
.title {{ text-align: center; font-size: 1.5em; font-weight: bold; margin: 1em 0; }}
.section {{ margin: 2em 0; }}
.title4 {{ margin: 1em 0; }}
.title-p {{ font-weight: bold; font-size: 1.2em; }}
.p {{ margin: 0.5em 0; text-indent: 1em; }}
.img {{ text-align: center; margin: 1em 0; }}
</style>
</head>
<body>
<div class="title">{day_name}</div>
'''.format(day_name=day_name)

    # Добавляем главы
    for chapter_ref in day_data['chapters']:
        parsed = parse_chapter_reference(chapter_ref)
        if not parsed:
            print(f"Не удалось распарсить ссылку: {chapter_ref}")
            continue

        book_abbr, chapter_num, verse_start, verse_end = parsed

        # Находим книгу в маппинге
        if book_abbr not in BOOK_MAPPING:
            print(f"Книга не найдена в маппинге: {book_abbr}")
            continue

        book_name, book_file = BOOK_MAPPING[book_abbr]

        # Извлекаем главу
        chapter_div = extract_chapter_from_xhtml(epub_dir, book_file, chapter_num)

        if chapter_div is not None:
            # Добавляем название книги и главы
            html_content += f'<div class="section">\n'
            html_content += f'<div class="title4"><p class="title-p">{book_name}. Глава {chapter_num}</p></div>\n'

            # Извлекаем содержимое главы
            for elem in chapter_div:
                html_content += etree.tostring(elem, encoding='unicode', method='html')

            html_content += '</div>\n'

    html_content += '</body></html>'

    # Создаем EPUB главу
    c1 = epub.EpubHtml(title=day_name, file_name='content.xhtml', lang='ru')
    c1.content = html_content

    # Добавляем главу в книгу
    book.add_item(c1)

    # Создаем оглавление
    book.toc = (epub.Link('content.xhtml', day_name, 'content'),)

    # Добавляем стандартные файлы навигации
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Определяем spine
    book.spine = ['nav', c1]

    # Сохраняем EPUB
    output_path = os.path.join(output_dir, f'day_{day_num:03d}.epub')
    epub.write_epub(output_path, book)
    print(f"Создан: {output_path}")


def main():
    # Пути
    days_file = 'days'
    epub_dir = 'epub_extracted'
    output_dir = 'daily_epubs'

    # Создаем выходную директорию
    os.makedirs(output_dir, exist_ok=True)

    # Парсим файл с днями
    print("Парсинг файла days...")
    days = parse_days_file(days_file)
    print(f"Найдено дней: {len(days)}")

    # Генерируем EPUB для каждого дня
    for day_name, day_data in sorted(days.items(), key=lambda x: x[1]['number']):
        print(f"\nГенерация {day_name}...")
        create_daily_epub(day_name, day_data, epub_dir, output_dir)

    print(f"\n✓ Готово! Создано {len(days)} EPUB файлов в папке {output_dir}/")


if __name__ == '__main__':
    main()
