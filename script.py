import argparse
import json
import os
from urllib.parse import urljoin, urlsplit

from parse_tululu_category import parse_category
import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from tqdm import trange


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def parse_book_name(book_soup):
    title_soup = book_soup.select_one('#content h1')

    title, author = title_soup.text.strip().split('::')
    return title.strip(), author.strip()


def download_txt(base_url, title, book_number, folder):
    book_number = int(sanitize_filename(book_number))
    folder = os.path.join(folder)
    os.makedirs(folder, exist_ok=True)
    book = os.path.join(folder, f'{title}.txt')
    payload = {'id': book_number}
    text_response = requests.get(f'{base_url}txt.php', params=payload)
    text_response.raise_for_status()
    with open(book, 'w', encoding='utf-8') as text_file:
        text_file.write(text_response.text)


def download_book_image(soup, base_url, folder):
    folder = os.path.join(folder)
    os.makedirs(folder, exist_ok=True)
    image_src = soup.select_one('div.bookimage img')['src']
    if 'nopic.gif' not in sanitize_filename(image_src):
        image_url = urljoin(base_url, image_src)
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        image = os.path.join(folder, sanitize_filename(image_src))
        with open(image, 'wb') as image_file:
            image_file.write(image_response.content)
        return image_url


def parse_book_genre(book_soup):
    genres_soup = book_soup.select('span.d_book a')
    genres = [genre.text for genre in genres_soup]
    return genres


def parse_comments(book_soup):
    comments = book_soup.select('div.texts span')
    if comments:
        comment_text = [comment.text for comment in comments]
        return comment_text


def parse_book_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--start_id',
        type=int,
        default=1,
        help='Первая страница',
    )
    parser.add_argument(
        '--end_id',
        type=int,
        default=100,
        help='Последняя страница',
    )
    return parser.parse_args()


def main():
    args = parse_book_args()
    base_url = 'https://tululu.org/'
    scifi_url = 'https://tululu.org/l55/'
    books_info = []
    for number in trange(1, 5):
        if number == 1:
            url = scifi_url
        else:
            url = urljoin(scifi_url, '{}/'.format(number))
        response = requests.get(url)
        response.raise_for_status()
        check_for_redirect(response)
        soup = BeautifulSoup(response.text, 'lxml')
        book_urls = parse_category(base_url, soup)
        for book_url in book_urls:
            book_response = requests.get(book_url)
            book_response.raise_for_status()
            check_for_redirect(book_response)
            book_soup = BeautifulSoup(book_response.text, 'lxml')
            title, author = parse_book_name(book_soup)
            book_number = urlsplit(book_url).path.replace('b', '')
            download_txt(base_url, title, book_number, folder='books/')
            genre = parse_book_genre(book_soup)
            comments = parse_comments(book_soup)
            image_src = download_book_image(book_soup, base_url, folder='covers/')
            page_info = {'Автор': author,
                         'Заголовок': title,
                         'Ссылка на книгу': book_url,
                         'Ссылка на обложку': image_src,
                         'Жанр': genre,
                         'Комментарии': comments,
                         }
            books_info.append(page_info)
    with open('books_info.json', 'w+', encoding='utf8') as book_file:
        json.dump(books_info, book_file, ensure_ascii=False, indent=4, sort_keys=True)


if __name__ == '__main__':
    main()
