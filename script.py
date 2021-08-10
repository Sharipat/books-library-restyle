import requests
import os
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def check_for_directory(filepath):
    try:
        os.makedirs(filepath)
    except FileExistsError:
        return


def check_for_redirect(url, i):
    response = requests.head(url.format(i), allow_redirects=True)
    response.raise_for_status()
    if response.history:
        raise requests.HTTPError


def parse_book_name(i):
    response = requests.get(f'https://tululu.org/b{i}')
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    title, author = soup.find('h1').text.strip().split(sep='\xa0 :: \xa0 ')
    title = sanitize_filename(title)
    return title


def parse_book_image(url, folder, name, i):
    response = requests.get(f'https://tululu.org/b{i}')
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'lxml')
    image_url = soup.find('img', class_='book-image')['src']
    if 'nopic' is not in image_url:
        


def download_txt(url, folder):
    for i in range(1, 11):
        try:
            check_for_redirect(url, i)
            name = parse_book_name(i)
            book = os.path.join(folder, f'{i}. {name}.txt')
            response = requests.get(url.format(i))
            response.raise_for_status()
            with open(book, 'wb') as file:
                file.write(response.content)

        except requests.HTTPError:
            continue
    print('Your books are ready!')


def test(folder, url, name):
    name = sanitize_filename(name)
    print(name)
    book = os.path.join(folder, f'{name}.txt')
    response = requests.get(url.format(4))
    response.raise_for_status()
    with open(book, 'wb') as file:
        file.write(response.content)


def main():
    url = "https://tululu.org/txt.php?id={}"
    folder = 'books'
    check_for_directory(folder)
    download_txt(url, folder)
    # test(folder, url, 'Али\\би')


if __name__ == '__main__':
    main()
