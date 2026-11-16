import json
import os
from models import Book

class JSONStorage:
    def __init__(self, filename="books.json"):
        self.filename = filename

    def load_books(self):
        if not os.path.exists(self.filename):
            return []
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [Book.from_dict(item) for item in data]
        except json.JSONDecodeError:
            return []

    def save_books(self, books):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump([book.to_dict() for book in books], f, ensure_ascii=False, indent=4)
