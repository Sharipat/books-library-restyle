import requests
import os


def get_book(url, filepath, name):
        try:
            os.makedirs(filepath)
        except FileExistsError:
            for i in range(1, 11):
                book = filepath+name.format(i)
                response = requests.post(url.format(i))
                response.raise_for_status()
                with open(book, 'wb') as file:
                    file.write(response.content)


def main():
    url = "https://tululu.org/txt.php?id={}"
    filepath = f'../books/'
    name = 'id{}.txt'
    get_book(url, filepath, name)


if __name__ == '__main__':
    main()
