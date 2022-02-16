import argparse
import json
import os
import time
from collections import Counter

import bs4
import regex as re
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    ElementNotVisibleException,
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By

RATING_STARS_DICT = {
    "it was amazing": 5,
    "really liked it": 4,
    "liked it": 3,
    "it was ok": 2,
    "did not like it": 1,
    "": None,
}


def switch_reviews_mode(driver, book_id, sort_order="default", rating=""):
    """
    Copyright (C) 2019 by Omar Einea: https://github.com/OmarEinea/GoodReadsScraper
    Licensed under GPL v3.0: https://github.com/OmarEinea/GoodReadsScraper/blob/master/LICENSE.md
    Accessed on 2019-12-01.
    """
    edition_reviews = False
    driver.execute_script(
        'document.getElementById("reviews").insertAdjacentHTML("beforeend", \'<a data-remote="true" rel="nofollow"'
        f'class="actionLinkLite loadingLink" data-keep-on-success="true" id="switch{rating}{sort_order}"'
        + f'href="/book/reviews/{book_id}?rating={rating}&sort={sort_order}'
        + ("&edition_reviews=true" if edition_reviews else "")
        + "\">Switch Mode</a>');"
        + f'document.getElementById("switch{rating}{sort_order}").click()'
    )
    return True


def get_rating(node):
    if len(node.find_all("span", {"class": "staticStars"})) > 0:
        rating = node.find_all("span", {"class": "staticStars"})[0]["title"]
        return RATING_STARS_DICT[rating]
    return ""


def get_user_name(node):
    if len(node.find_all("a", {"class": "user"})) > 0:
        return node.find_all("a", {"class": "user"})[0]["title"]
    return ""


def get_user_url(node):
    if len(node.find_all("a", {"class": "user"})) > 0:
        return node.find_all("a", {"class": "user"})[0]["href"]
    return ""


def get_date(node):
    if len(node.find_all("a", {"class": "reviewDate createdAt right"})) > 0:
        return node.find_all("a", {"class": "reviewDate createdAt right"})[0].text
    return ""


def get_text(node):

    display_text = ""
    full_text = ""

    if len(node.find_all("span", {"class": "readable"})) > 0:
        for child in node.find_all("span", {"class": "readable"})[0].children:
            if child.name == "span" and "style" not in child:
                display_text = child.text
            if (
                child.name == "span"
                and "style" in child
                and child["style"] == "display:none"
            ):
                full_text = child.text

    if full_text:
        return full_text

    return display_text


def get_num_likes(node):
    if (
        node.find("span", {"class": "likesCount"})
        and len(node.find("span", {"class": "likesCount"})) > 0
    ):
        likes = node.find("span", {"class": "likesCount"}).text
        if "likes" in likes:
            return int(likes.split()[0])
    return 0


def get_shelves(node):
    shelves = []
    if node.find("div", {"class": "uitext greyText bookshelves"}):
        _shelves_node = node.find("div", {"class": "uitext greyText bookshelves"})
        for _shelf_node in _shelves_node.find_all("a"):
            shelves.append(_shelf_node.text)
    return shelves


def get_id(bookid):
    pattern = re.compile("([^.]+)")
    return pattern.search(bookid).group()


def scrape_reviews_on_current_page(driver, url, book_id, sort_order="newest"):

    reviews = []

    # Pull the page source, load into BeautifulSoup, and find all review nodes.
    source = driver.page_source
    soup = bs4.BeautifulSoup(source, "lxml")
    nodes = soup.find_all("div", {"class": "review"})
    book_title = soup.find(id="bookTitle").text.strip()

    # Iterate through and parse the reviews.
    for node in nodes:
        review_id = re.search("[0-9]+", node["id"]).group(0)
        shelves = get_shelves(node)
        if not shelves:
            continue

        reviews.append(
            {
                "book_id_title": book_id,
                "book_id": get_id(book_id),
                "book_title": book_title,
                "review_url": f"https://www.goodreads.com/review/show/{review_id}",
                "review_id": review_id,
                "date": get_date(node),
                "rating": get_rating(node),
                "user_name": get_user_name(node),
                "user_url": get_user_url(node),
                "num_likes": get_num_likes(node),
                "sort_order": sort_order,
                "shelves": get_shelves(node),
            }
        )

    return reviews


def check_for_duplicates(reviews):
    review_ids = [r["review_id"] for r in reviews]
    num_duplicates = len(
        [_id for _id, _count in Counter(review_ids).items() if _count > 1]
    )
    return num_duplicates


def get_reviews(driver: webdriver.Chrome, book_id: str, pages: int = 1):
    reviews = []
    url = "https://www.goodreads.com/book/show/" + book_id
    driver.get(url)

    try:
        print("Scraping the first page of reviews.")
        reviews = scrape_reviews_on_current_page(driver, url, book_id)
        print("Scraped page 1")

        # GoodReads will only load the first 10 pages of reviews.
        # Click through each of the following nine pages and scrape each page.
        page_counter = 2
        while page_counter <= pages:
            try:
                if driver.find_element(By.LINK_TEXT, str(page_counter)):
                    driver.find_element(By.LINK_TEXT, str(page_counter)).click()
                    time.sleep(3)
                    reviews += scrape_reviews_on_current_page(driver, url, book_id)
                    print(f"Scraped page {page_counter}")
                    page_counter += 1
                else:
                    return reviews

            except NoSuchElementException:
                if page_counter == 10:
                    try:
                        driver.find_element(By.LINK_TEXT, str(9)).click()
                        time.sleep(2)
                        continue
                    except Exception:
                        return reviews
                else:
                    print(f"{book_id} has less than 10 pages of reviews!")
                    return reviews

            except ElementNotVisibleException:
                print(
                    "ERROR ElementNotVisibleException: Pop-up detected, reloading the page."
                )
                reviews = get_reviews(driver, book_id)
                return reviews

            except ElementClickInterceptedException:
                print(
                    f"🚨 ElementClickInterceptedException (Likely a pop-up)🚨\n🔄 Refreshing Goodreads site and skipping problem page {page_counter}🔄"
                )
                driver.get(url)
                time.sleep(3)
                page_counter += 1
                continue

            except StaleElementReferenceException:
                print(
                    "ERROR: StaleElementReferenceException\nRefreshing Goodreads site and skipping problem page {page_counter} "
                )
                driver.get(url)
                time.sleep(3)
                page_counter += 1
                continue

    except ElementClickInterceptedException:
        print(
            "🚨 ElementClickInterceptedException (Likely a pop-up)🚨\n🔄 Refreshing Goodreads site and rescraping book🔄"
        )
        driver.get(url)
        time.sleep(3)
        reviews = get_reviews(driver, book_id)
        return reviews

    except ElementNotInteractableException:
        print(
            "🚨 ElementNotInteractableException🚨 \n🔄 Refreshing Goodreads site and rescraping book🔄"
        )
        reviews = get_reviews(driver, book_id)
        return reviews

    if check_for_duplicates(reviews) >= 30:
        print(
            f"ERROR: {check_for_duplicates(reviews)} duplicates found! Re-scraping this book."
        )
        reviews = get_reviews(driver, book_id)
        return reviews
    else:
        return reviews

    return reviews


def condense_reviews(reviews_directory_path):
    reviews = []
    for file_name in os.listdir(reviews_directory_path):
        if (
            file_name.endswith(".json")
            and not file_name.startswith(".")
            and file_name != "all_reviews.json"
        ):
            _reviews = json.load(open(reviews_directory_path + "/" + file_name, "r"))
            reviews += _reviews
    return reviews


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
    parser.add_argument("--review-pages", type=int, help="Number of pages", default=1)
    args = parser.parse_args()

    driver = initialize_driver()
    results = get_reviews(driver, args.book_id, pages=args.review_pages)
    print(results)
    driver.quit()


if __name__ == "__main__":
    main()
