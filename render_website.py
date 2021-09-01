import collections
import os

from more_itertools import chunked
import pandas
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server


def get_books(json_path):
    books_from_json = pandas.read_json(json_path).to_dict(orient='records')
    books = collections.defaultdict(list)
    for book in books_from_json:
        books[book['title']].append(book)
    return sorted(books.items())


def render_page(env, books, dest_folder, pages_folder):
    folder = os.path.join(dest_folder, pages_folder)
    os.makedirs(folder, exist_ok=True)
    template = env.get_template('template.html')
    chunked_books = chunked(books, 10)
    for number, page in enumerate(chunked_books, 1):
        page_path = os.path.join(folder, f'index{number}.html')
        rendered_page = template.render(books_catalog=page)
        with open(page_path, 'w', encoding="utf8") as file:
            file.write(rendered_page)


def main():
    load_dotenv()
    env = Environment(
        loader=FileSystemLoader('templates'),
        autoescape=select_autoescape(['html', 'xml']))
    json_path = os.getenv('JSON_PATH')
    dest_folder = os.getenv('DEST_FOLDER')
    pages_folder = os.getenv('PAGES_FOLDER')
    books = get_books(json_path)
    render_page(env, books, dest_folder, pages_folder)
    server = Server()
    server.watch('template.html', render_page)
    server.serve(root='.')


if __name__ == '__main__':
    main()
