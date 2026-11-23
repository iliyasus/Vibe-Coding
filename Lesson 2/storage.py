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
Файл: main.py
from storage import JSONStorage


def main():
    storage = JSONStorage()
    
    while True:
        print("\n--- Учёт книг ---")
        print("1. Добавить книгу")
        print("2. Показать все книги")
        print("3. Удалить книгу")
        print("4. Выйти")
        
        choice = input("Выберите действие (1-4): ")
        
        if choice == "1":
            title = input("Введите название книги: ")
            author = input("Введите автора: ")
            year = input("Введите год издания: ")
            
            books = storage.load_books()
            books.append(Book(title, author, year))
            storage.save_books(books)
            print("Книга успешно добавлена!")
            
        elif choice == "2":
            books = storage.load_books()
            if not books:
                print("Список книг пуст.")
            else:
                print("\nСписок книг:")
                for idx, book in enumerate(books, 1):
                    print(f"{idx}. \"{book.title}\" — {book.author} ({book.year} г.)")
                    
        elif choice == "3":
            books = storage.load_books()
            if not books:
                print("Список книг пуст, нечего удалять.")
                continue
                
            for idx, book in enumerate(books, 1):
                print(f"{idx}. \"{book.title}\" — {book.author}")
                
            try:
                num = int(input("Введите номер книги для удаления: "))
                if 1 <= num <= len(books):
                    removed = books.pop(num - 1)
                    storage.save_books(books)
                    print(f"Книга \"{removed.title}\" удалена.")
                else:
                    print("Неверный номер.")
            except ValueError:
                print("Введите корректное число.")
                
        elif choice == "4":
            print("Выход из программы.")
            break
        else:
            print("Неверный пункт меню, попробуйте снова.")

if __name__ == "__main__":
    main()
