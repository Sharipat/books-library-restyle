import os
import urllib.parse

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def parse_book_name(response):
    soup = BeautifulSoup(response.text, 'lxml')
    title_soup = soup.find('div', id='content')
    if title_soup:
        title_text = title_soup.find('h1').text
        title, author = title_text.strip().split(' :: ')
        return sanitize_filename(title).strip()


def download_txt(url, title, number, folder):
    folder = os.path.join(folder)
    os.makedirs(folder, exist_ok=True)
    book = os.path.join(folder, f'{number}. {title}.txt')
    book_url = '{}txt.php?id={}'.format(url, number)
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


def parse_book_image(response):
    soup = BeautifulSoup(response.content, 'lxml')
    image_soup = soup.select_one('div.bookimage img')['src']
    return image_soup


def download_book_image(image_soup, url, folder):
    folder = os.path.join(folder)
    os.makedirs(folder, exist_ok=True)
    image_url = urllib.parse.urljoin(url, image_soup)
    image_response = requests.get(image_url)
    image_response.raise_for_status()
    image = os.path.join(folder, sanitize_filename(image_soup))
    with open(image, 'wb') as image_file:
        image_file.write(image_response.content)


def main():
    url = 'https://tululu.org/'
    for number in range(1, 11):
        name_url = urllib.parse.urljoin(url, 'b{}/'.format(number))
        try:
            response = requests.get(name_url)
            response.raise_for_status()
            title = parse_book_name(response)
            if title:
                download_txt(url, title, number, folder='books/')
                download_comments(response, number, folder='comments/')
                image_soup = parse_book_image(response)
                if 'nopic.gif' not in sanitize_filename(image_soup):
                    download_book_image(image_soup, url, folder='covers/')
        except requests.HTTPError:
            print(f'No page at {name_url}')


if __name__ == '__main__':
    main()
