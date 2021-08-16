import argparse
import logging
import os
from urllib.parse import urljoin, urlencode

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from tqdm import trange


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def parse_book_name(soup):
    title_soup = soup.find('div', id='content')
    title_text = title_soup.find('h1').text.strip().split(' :: ')
    title, author = title_text
    return title.strip(), author.strip()


def download_txt(base_url, title, number, folder):
    folder = os.path.join(folder)
    os.makedirs(folder, exist_ok=True)
    book = os.path.join(folder, f'{number}. {title}.txt')
    payload = {'txt.php': f'id={number}'}
    text_response = requests.get(base_url, params=payload)
    text_response.raise_for_status()
    with open(book, 'w+') as file:
        file.write(text_response.text)


def parse_comments(soup):
    comments = soup.select('div.texts span')
    if comments:
        comment_text = [comment for comment in comments]
        return comment_text


def parse_book_genre(soup):
    genres_soup = soup.select('span.d_book a')
    genres = [genre for genre in genres_soup]
    return genres


def parse_book_image(response):
    soup = BeautifulSoup(response.content, 'lxml')
    return soup.select_one('div.bookimage img')['src']


def download_book_image(image_src, url, folder):
    folder = os.path.join(folder)
    os.makedirs(folder, exist_ok=True)
    image_url = urljoin(url, image_src)
    image_response = requests.get(image_url)
    image_response.raise_for_status()
    image = os.path.join(folder, sanitize_filename(image_src))
    with open(image, 'wb') as image_file:
        image_file.write(image_response.content)


def parse_book_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--start_id',
        type=int,
        default=1,
        help='Первая страница'
    )
    parser.add_argument(
        '--end_id',
        type=int,
        default=100,
        help='Последняя страница'
    )
    return parser.parse_args()


def main():
    args = parse_book_args()
    base_url = 'https://tululu.org/'
    for number in trange(args.start_id, (args.end_id + 1)):
        url = urlencode(urljoin(base_url, 'b{}/'.format(number)))
        try:
            response = requests.get(url)
            response.raise_for_status()
            check_for_redirect(response)
            soup = BeautifulSoup(response.text, 'lxml')
            title, author = parse_book_name(soup)
            download_txt(base_url, title, number, folder='books/')
            genre = parse_book_genre(soup)
            comments = parse_comments(soup)
            page_info = {'Автор: ': author,
                         'Заголовок: ': title,
                         'Жанр: ': genre,
                         'Комментарии: ': comments
                         }
            logging.info(page_info)
            image_src = parse_book_image(response)
            if 'nopic.gif' not in sanitize_filename(image_src):
                download_book_image(image_src, base_url, folder='covers/')
        except requests.HTTPError:
            print(f'No page at {url}')


if __name__ == '__main__':
    main()
