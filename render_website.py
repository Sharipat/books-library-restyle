import collections
import math
import os
from urllib.parse import unquote, urljoin

import pandas
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked

BOOKS_ON_PAGE = 10


def get_books(json_path):
    books_from_json = pandas.read_json(json_path).to_dict(orient='records')
    books = collections.defaultdict(list)
    for book in books_from_json:
        books[book['title']].append(book)
    return sorted(books.items())


def render_page(env, books, dest_folder, pages_folder, static_url):
    folder = os.path.join(dest_folder, pages_folder)
    os.makedirs(folder, exist_ok=True)
    template = env.get_template('template.html')
    chunked_books = list(chunked(books, BOOKS_ON_PAGE))
    pages_number = math.ceil(len(chunked_books))
    covers_path = urljoin(dest_folder, 'covers/nopic.gif')
    covers_url = unquote(covers_path)
    for number, page in enumerate(chunked_books, 1):
        page_path = os.path.join(folder, f'index{number}.html')
        previous_page = os.path.join(f'index{number - 1}.html') if number - 1 > 0 else None
        next_page = os.path.join(f'index{number + 1}.html') if number + 1 <= pages_number else None
        all_pages = [
            {'number': number, 'url': os.path.join(f'index{number}.html')
             } for number in range(1, pages_number + 1)]
        rendered_page = template.render(static_url=static_url, covers_url=covers_url,
                                        books_catalog=page, next_page=next_page, previous_page=previous_page,
                                        all_pages=all_pages)
        with open(page_path, 'w', encoding="utf8") as page_file:
            page_file.write(rendered_page)


def main():
    load_dotenv()
    env = Environment(
        loader=FileSystemLoader('templates'),
        autoescape=select_autoescape(['html', 'xml']))
    json_path = os.getenv('JSON_PATH', 'book_info.json')
    dest_folder = os.getenv('DEST_FOLDER', 'library')
    pages_folder = os.getenv('PAGES_FOLDER', 'pages')
    static_url = os.getenv('STATIC_URL')
    books = get_books(json_path)
    render_page(env, books, dest_folder, pages_folder, static_url)
    server = Server()
    server.watch('template.html', render_page)
    server.serve(root='.')


if __name__ == '__main__':
    main()
