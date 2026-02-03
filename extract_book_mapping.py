#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Извлекает маппинг книг из toc.ncx
"""

from lxml import etree

def extract_book_mapping(toc_path):
    """Извлекает маппинг книг из toc.ncx"""
    parser = etree.XMLParser(encoding='utf-8')
    tree = etree.parse(toc_path, parser)
    root = tree.getroot()

    # Namespace для NCX
    ns = {'ncx': 'http://www.daisy.org/z3986/2005/ncx/'}

    # Находим все navPoint
    nav_points = root.xpath('//ncx:navPoint', namespaces=ns)

    books = {}
    current_book = None

    for nav_point in nav_points:
        # Получаем текст навигации
        label = nav_point.xpath('.//ncx:text', namespaces=ns)
        if label:
            label_text = label[0].text

        # Получаем ссылку на файл
        content = nav_point.xpath('.//ncx:content', namespaces=ns)
        if content:
            src = content[0].get('src')
            file_name = src.split('#')[0]

            # Проверяем, является ли это названием книги (не главой)
            if not label_text.startswith('Glava '):
                # Это название книги
                if current_book != label_text:
                    current_book = label_text
                    books[current_book] = file_name
                    print(f"{current_book} -> {file_name}")

    return books

if __name__ == '__main__':
    toc_path = 'epub_extracted/OEBPS/toc.ncx'
    extract_book_mapping(toc_path)
