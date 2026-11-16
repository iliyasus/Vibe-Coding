from models import Book
from storage import JSONStorage


def filter_books(books, genre):
    genre = genre.strip().casefold()
    return [
        book for book in books
        if (book.genre or "Без жанра").strip().casefold() == genre
    ]


def main():
    storage = JSONStorage()

    while True:
        print("\n--- Учёт книг ---")
        print("1. Добавить книгу")
        print("2. Показать все книги")
        print("3. Удалить книгу")
        print("4. Фильтровать по жанру")
        print("5. Выйти")

        choice = input("Выберите действие (1-5): ")

        if choice == "1":
            title = input("Введите название книги: ")
            author = input("Введите автора: ")
            year = input("Введите год издания: ")
            genre = input("Введите жанр: ").strip()

            books = storage.load_books()
            books.append(Book(title, author, year, genre))
            storage.save_books(books)
            print("Книга успешно добавлена!")

        elif choice == "2":
            books = storage.load_books()
            if not books:
                print("Список книг пуст.")
            else:
                print("\nСписок книг:")
                for idx, book in enumerate(books, 1):
                    genre = book.genre or "Без жанра"
                    print(
                        f'{idx}. "{book.title}" — {book.author} '
                        f"({book.year} г.), жанр: {genre}"
                    )

        elif choice == "3":
            books = storage.load_books()
            if not books:
                print("Список книг пуст, нечего удалять.")
                continue

            for idx, book in enumerate(books, 1):
                print(f'{idx}. "{book.title}" — {book.author}')

            try:
                num = int(input("Введите номер книги для удаления: "))
                if 1 <= num <= len(books):
                    removed = books.pop(num - 1)
                    storage.save_books(books)
                    print(f'Книга "{removed.title}" удалена.')
                else:
                    print("Неверный номер.")
            except ValueError:
                print("Введите корректное число.")

        elif choice == "4":
            books = storage.load_books()
            genre = input("Введите жанр для фильтрации: ")
            filtered_books = filter_books(books, genre)
            if not filtered_books:
                print("Книги этого жанра не найдены.")
            else:
                print("\nСписок книг:")
                for idx, book in enumerate(filtered_books, 1):
                    book_genre = book.genre or "Без жанра"
                    print(
                        f'{idx}. "{book.title}" — {book.author} '
                        f"({book.year} г.), жанр: {book_genre}"
                    )

        elif choice == "5":
            print("Выход из программы.")
            break
        else:
            print("Неверный пункт меню, попробуйте снова.")


if __name__ == "__main__":
    main()
