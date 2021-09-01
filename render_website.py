import collections
import os

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


def render_page(env, books):
    template = env.get_template('template.html')
    rendered_page = template.render(books_catalog=books)
    with open('index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)


def main():
    load_dotenv()
    env = Environment(
        loader=FileSystemLoader('templates'),
        autoescape=select_autoescape(['html', 'xml']))
    json_path = os.getenv('JSON_PATH')
    books = get_books(json_path)
    render_page(env, books)
    server = Server()
    server.watch('template.html', render_page)
    server.serve(root='.')


if __name__ == '__main__':
    main()