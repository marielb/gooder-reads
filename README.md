# gooder-reads
Goodreads, but gooder

# description
Something I've been doing manually to get book recommendations is looking at the reviews of a book I recently enjoyed, click on the "favorites" shelves that they are on, and perusing the other books on those shelves.

This script aggregates those commmonly favorited books and ranks them.

# usage
1. Go to the book page for one of your favorite books.
2. Get the book ID from the URL e.g. 50202953
3. Run the recommend_books.py script
``dc run books-pls python recommend_books.py --book-id 50202953 --pages 5``

# credit
Uses scraping logic from https://github.com/maria-antoniak/goodreads-scraper , licensed under GPL v3.0.
