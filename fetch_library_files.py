import argparse
import json
import os
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename, sanitize_file_path
from tqdm import trange

from parse_tululu_category import parse_category


def get_last_page(scifi_url):
    page_response = requests.get(scifi_url)
    page_response.raise_for_status()
    page_soup = BeautifulSoup(page_response.text, 'lxml')
    last_page = page_soup.select_one('a.npage:last-of-type').text
    return int(last_page)


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def parse_book_name(book_soup):
    title_soup = book_soup.select_one('#content h1')
    title, author = title_soup.text.strip().split('::')
    return title.strip()[0:35], author.strip()


def download_txt(base_url, title, book_number, dest_folder, folder):
    book_title = sanitize_filename(title.strip())
    book_number = int(sanitize_filename(book_number))
    folder = os.path.join(dest_folder, folder)
    os.makedirs(folder, exist_ok=True)
    book = urljoin(folder, f'{book_title}.txt').replace('...', '')
    payload = {'id': book_number}
    text_response = requests.get(f'{base_url}txt.php', params=payload)
    text_response.raise_for_status()
    if text_response.history:
        book = None
    else:
        with open(book, 'w', encoding='utf-8') as text_file:
            text_file.write(text_response.text)
    return book


def download_book_image(soup, base_url, dest_folder, folder):
    folder = os.path.join(dest_folder, folder)
    os.makedirs(folder, exist_ok=True)
    image_src = soup.select_one('div.bookimage img')['src']
    if 'nopic.gif' not in sanitize_filename(image_src):
        image_url = urljoin(base_url, image_src)
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        image = os.path.join(folder, sanitize_filename(image_src))
        with open(image, 'wb') as image_file:
            image_file.write(image_response.content)
        return image


def parse_book_genre(book_soup):
    genres_soup = book_soup.select('span.d_book a')
    genres = [genre.text for genre in genres_soup]
    return genres


def parse_comments(book_soup):
    comments = book_soup.select('div.texts span')
    if comments:
        comment_text = [comment.text for comment in comments]
        return comment_text


def parse_book_args(last_page):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--start_page',
        type=int,
        default=1,
        help='Первая страница',
    )
    parser.add_argument(
        '--end_page',
        type=int,
        default=last_page + 1,
        help='Последняя страница',
    )
    parser.add_argument(
        '--dest_folder',
        help='Путь к каталогу',
        default='library',
        type=str
    )
    parser.add_argument(
        '--skip_imgs',
        help='Не скачивать обложки книг',
        action='store_true'
    )

    parser.add_argument(
        '--skip_txt',
        help='Не скачивать книги',
        action='store_true'
    )
    parser.add_argument(
        '--json_path',
        help='путь к файлу json',
        default='book_info.json',
        type=str
    )

    return parser.parse_args()


def main():
    base_url = 'https://tululu.org/'
    scifi_url = 'https://tululu.org/l55/'
    last_page = get_last_page(scifi_url)
    args = parse_book_args(last_page)
    books_info = []
    for number in trange(args.start_page, args.end_page+1):
        url = urljoin(scifi_url, '{}/'.format(number))
        response = requests.get(url)
        response.raise_for_status()
        check_for_redirect(response)
        soup = BeautifulSoup(response.text, 'lxml')
        book_urls = parse_category(url, soup)
        for book_url in book_urls:
            book_response = requests.get(book_url)
            try:
                book_response.raise_for_status()
                check_for_redirect(book_response)
            except requests.HTTPError:
                print(f'No page at {book_url}')
            book_soup = BeautifulSoup(book_response.text, 'lxml')
            title, author = parse_book_name(book_soup)
            book_number = urlsplit(book_url).path.replace('b', '')
            genre = parse_book_genre(book_soup)
            comments = parse_comments(book_soup)
            if not args.skip_txt:
                book_src = download_txt(base_url, title, book_number, args.dest_folder, folder='books/')
            else:
                book_src = None
            if not args.skip_imgs:
                image_src = download_book_image(book_soup, base_url, args.dest_folder, folder='covers/')
            else:
                image_src = None
            page_info = {'author': author,
                         'title': title,
                         'book_src': book_src,
                         'image_src': image_src,
                         'genre': genre,
                         'comments': comments,
                         }
            if page_info['book_src']:
                books_info.append(page_info)
    with open(args.json_path, 'w+', encoding='utf8') as book_file:
        json.dump(books_info, book_file, ensure_ascii=False, indent=4, sort_keys=True)


if __name__ == '__main__':
    main()
