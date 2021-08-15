import argparse
import os
from urllib.parse import urljoin
from tqdm import trange

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError
    return response


def parse_book_name(response):
    soup = BeautifulSoup(response.text, 'lxml')
    title_soup = soup.find('div', id='content')
    if title_soup:
        title_text = title_soup.find('h1').text.strip().split(' :: ')
        title = sanitize_filename(title_text[0].strip())
        author = sanitize_filename(title_text[1].strip())
        title_tuple = (title, author,)
        return title_tuple


def download_txt(url, title, number, folder):
    folder = os.path.join(folder)
    os.makedirs(folder, exist_ok=True)
    book = os.path.join(folder, f'{number}. {title}.txt')
    book_url = urljoin(url, 'txt.php?id={}'.format(number))
    text_response = requests.get(book_url)
    text_response.raise_for_status()
    try:
        with open(book, 'wb') as file:
            file.write(text_response.content)
    except FileExistsError:
        return


def download_comments(response, number, folder):
    folder = os.path.join(folder)
    os.makedirs(folder, exist_ok=True)
    soup = BeautifulSoup(response.text, 'lxml')
    comments = soup.find_all('div', class_='texts')
    if comments:
        comments_path = os.path.join(folder, f'{number}.txt')
        with open(comments_path, 'w+') as comment_file:
            for comment in comments:
                comment_text = comment.find('span', class_='black').text
                comment_file.write(comment_text + '\n')
        return comment_text


def parse_book_genre(response):
    soup = BeautifulSoup(response.text, 'lxml')
    genres_soup = soup.find_all('div', id='content')
    genres = []
    for genre in genres_soup:
        genre = genre.find('span', class_='d_book').text.strip().split(': \xa0')
        genres.append(sanitize_filename(genre[1]))
    return genres


def parse_book_image(response):
    soup = BeautifulSoup(response.content, 'lxml')
    return soup.select_one('div.bookimage img')['src']


def download_book_image(image_soup, url, folder):
    folder = os.path.join(folder)
    os.makedirs(folder, exist_ok=True)
    image_url = urljoin(url, image_soup)
    image_response = requests.get(image_url)
    image_response.raise_for_status()
    image = os.path.join(folder, sanitize_filename(image_soup))
    with open(image, 'wb') as image_file:
        image_file.write(image_response.content)


def parse_book_page(title, author, genre, comments):
    page_info = {'Автор: ': author,
                 'Заголовок: ': title,
                 'Жанр: ': genre,
                 'Комментарии: ': comments
                 }
    return page_info


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
    url = 'https://tululu.org/'
    for number in trange(args.start_id, args.end_id):
        name_url = urljoin(url, 'b{}/'.format(number))
        try:
            response = requests.get(name_url)
            response.raise_for_status()
            if not response.history:
                title, author = parse_book_name(response)
                parse_book_genre(response)
                download_txt(url, title, number, folder='books/')
                genre = parse_book_genre(response)
                comments = download_comments(response, number, folder='comments/')
                page_info = parse_book_page(title, author, genre, comments)
                print(page_info)
                image_soup = parse_book_image(response)
                if 'nopic.gif' not in sanitize_filename(image_soup):
                    download_book_image(image_soup, url, folder='covers/')
        except requests.HTTPError:
            print(f'No page at {name_url}')


if __name__ == '__main__':
    main()
