from urllib.parse import urljoin


def parse_category(base_url, soup):
    book_urls = []
    category_soup = soup.find_all(class_='d_book')
    for book in category_soup:
        book_src = book.find('a')['href']
        book_url = urljoin(base_url, book_src)
        book_urls.append(book_url)
    return book_urls


