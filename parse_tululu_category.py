from urllib.parse import urljoin


def parse_category(base_url, soup):
    book_urls = []
    category_soup = soup.select('.d_book')
    for book in category_soup:
        book_src = book.select_one('a')['href']
        book_url = urljoin(base_url, book_src)

        book_urls.append(book_url)
    return book_urls
