import argparse
from collections import Counter

from selenium import webdriver

from get_books_on_shelf import get_books
from get_reviews import get_reviews


def get_recommendations(driver: webdriver.Chrome, book_id: str, pages: int = 1):
    reviews = get_reviews(driver, book_id, pages)
    filtered_shelves = [
        shelf["shelf_id"]
        for review in reviews
        for shelf in review["shelves"]
        if "favorite" in shelf["name"] or "favourite" in shelf["name"]
    ]
    print(filtered_shelves)
    books = []
    for shelf in filtered_shelves:
        print(f"Getting books for shelf {shelf}")
        books += list(get_books(driver, shelf, pages))
    counter = Counter(books)
    return counter.most_common(25)


def initialize_driver():
    print("Starting web driver")
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    return driver


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--book-id", type=str, help="Goodreads book ID of one of your favorite books."
    )
    parser.add_argument("--pages", type=int, help="Number of pages", default=1)
    args = parser.parse_args()

    driver = initialize_driver()
    results = get_recommendations(driver, args.book_id, pages=args.pages)
    for result in results:
        print(result)
    driver.quit()


if __name__ == "__main__":
    main()
