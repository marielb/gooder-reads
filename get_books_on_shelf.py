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


def scrape_books_on_current_page(driver, url, shelf_id, sort_order="newest"):
    books = set()

    # Pull the page source, load into BeautifulSoup, and find all review nodes.
    source = driver.page_source
    soup = bs4.BeautifulSoup(source, "lxml")
    nodes = soup.find_all("tr", {"class": "review"})

    # Iterate through and parse the books.
    for node in nodes:
        title_node = node.find_all("td", {"class": "title"})[0]
        book_title = title_node.find_all("a")[0]["title"]
        books.add(book_title)

    return books


def get_books(driver: webdriver.Chrome, shelf_id: str, pages: int = 1):
    books = set()
    url = "https://www.goodreads.com/review/list/" + shelf_id
    driver.get(url)

    last_height = driver.execute_script("return document.body.scrollHeight")
    count = 0

    while count < 5:
        count += 1
        print("scrolling")
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(2)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    books = scrape_books_on_current_page(driver, url, shelf_id)
    books.update(scrape_books_on_current_page(driver, url, shelf_id))

    return books



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
        "--shelf-id", type=str, help="Goodreads shelf ID"
    )
    args = parser.parse_args()

    driver = initialize_driver()
    results = get_books(driver, args.shelf_id)
    print(results)
    driver.quit()


if __name__ == "__main__":
    main()
