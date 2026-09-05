"""
Library Management System (with waitlist queue & return history stack)
------------------------------------------------------------------------
A console app for managing a small library's book catalog, issuing and
returning books, and handling a reservation waitlist when a book is
unavailable.

DSA concepts demonstrated:
  - Queue (FIFO) for the reservation waitlist -> first person to wait,
    first person to get the book back.
  - Stack (LIFO) for "recently returned" history -> most recent return
    shown first.
  - Binary search (manual) to find a book by ISBN once the catalog is
    kept sorted by ISBN.
  - Linear search for free-text title search.

Persistence: JSON file so the catalog survives between runs.
"""

import json
import os
from collections import deque

DATA_FILE = "library.json"


class Library:
    def __init__(self):
        self.books = []          # list of dicts: isbn, title, author, available
        self.waitlists = {}      # isbn -> deque of borrower names (the queue)
        self.return_history = [] # stack: most recent return on top (end of list)
        self._load()

    # ---------------- persistence ----------------
    def _load(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                self.books = data.get("books", [])
                self.waitlists = {k: deque(v) for k, v in data.get("waitlists", {}).items()}
                self.return_history = data.get("return_history", [])

    def save(self):
        data = {
            "books": self.books,
            "waitlists": {k: list(v) for k, v in self.waitlists.items()},
            "return_history": self.return_history,
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    # ---------------- catalog management ----------------
    def add_book(self, isbn, title, author):
        self.books.append({"isbn": isbn, "title": title, "author": author, "available": True})

    def _sorted_by_isbn(self):
        # insertion sort by isbn - keeps things simple and easy to explain
        arr = self.books[:]
        for i in range(1, len(arr)):
            key = arr[i]
            j = i - 1
            while j >= 0 and arr[j]["isbn"] > key["isbn"]:
                arr[j + 1] = arr[j]
                j -= 1
            arr[j + 1] = key
        return arr

    def find_by_isbn(self, isbn):
        """Binary search on the ISBN-sorted catalog."""
        arr = self._sorted_by_isbn()
        low, high = 0, len(arr) - 1
        while low <= high:
            mid = (low + high) // 2
            if arr[mid]["isbn"] == isbn:
                return arr[mid]
            elif arr[mid]["isbn"] < isbn:
                low = mid + 1
            else:
                high = mid - 1
        return None

    def find_by_title(self, title):
        """Linear search for partial title matches."""
        return [b for b in self.books if title.lower() in b["title"].lower()]

    # ---------------- issue / return (queue + stack in action) ----------------
    def issue_book(self, isbn, borrower):
        book = self.find_by_isbn(isbn)
        if book is None:
            return f"No book with ISBN {isbn}."

        if book["available"]:
            book["available"] = False
            return f"'{book['title']}' issued to {borrower}."
        else:
            # book unavailable -> join the waitlist queue
            self.waitlists.setdefault(isbn, deque())
            self.waitlists[isbn].append(borrower)
            position = len(self.waitlists[isbn])
            return f"'{book['title']}' is unavailable. {borrower} added to waitlist (position {position})."

    def return_book(self, isbn):
        book = self.find_by_isbn(isbn)
        if book is None:
            return f"No book with ISBN {isbn}."

        self.return_history.append(isbn)  # push onto the stack

        queue = self.waitlists.get(isbn)
        if queue:
            next_borrower = queue.popleft()  # dequeue - FIFO
            # book stays "unavailable" because it goes straight to the next borrower
            return f"'{book['title']}' returned and immediately issued to next in line: {next_borrower}."
        else:
            book["available"] = True
            return f"'{book['title']}' returned and is now available."

    def recent_returns(self, n=5):
        """Most recently returned books first (stack pop order, without mutating)."""
        recent_isbns = self.return_history[-n:][::-1]
        return [self.find_by_isbn(isbn) for isbn in recent_isbns]


# ---------------------------- CLI ----------------------------
def print_books(books):
    if not books:
        print("  (none)")
        return
    for b in books:
        status = "Available" if b["available"] else "Checked out"
        print(f"  [{b['isbn']}] {b['title']} — {b['author']} ({status})")


def menu():
    lib = Library()
    while True:
        print("\n--- Library Management System ---")
        print("1. Add book")
        print("2. View all books")
        print("3. Search by title (linear search)")
        print("4. Find by ISBN (binary search)")
        print("5. Issue book")
        print("6. Return book")
        print("7. View recent returns (stack)")
        print("8. Save & exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            isbn = input("ISBN: ").strip()
            title = input("Title: ")
            author = input("Author: ")
            lib.add_book(isbn, title, author)
            print("Book added.")

        elif choice == "2":
            print_books(lib.books)

        elif choice == "3":
            title = input("Title (or part of it): ")
            print_books(lib.find_by_title(title))

        elif choice == "4":
            isbn = input("ISBN: ").strip()
            book = lib.find_by_isbn(isbn)
            print(book if book else "Not found.")

        elif choice == "5":
            isbn = input("ISBN: ").strip()
            borrower = input("Borrower name: ")
            print(lib.issue_book(isbn, borrower))

        elif choice == "6":
            isbn = input("ISBN: ").strip()
            print(lib.return_book(isbn))

        elif choice == "7":
            print_books(lib.recent_returns())

        elif choice == "8":
            lib.save()
            print("Saved. Goodbye!")
            break

        else:
            print("Invalid option, try again.")


if __name__ == "__main__":
    menu()
