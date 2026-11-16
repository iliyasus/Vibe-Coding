import json

import main
from main import filter_books
from models import Book
from storage import JSONStorage


def test_book_serializes_genre():
    book = Book("Dune", "Frank Herbert", "1965", "Science fiction")

    assert book.to_dict() == {
        "title": "Dune",
        "author": "Frank Herbert",
        "year": "1965",
        "genre": "Science fiction"
    }


def test_book_loads_legacy_data_without_genre():
    book = Book.from_dict({
        "title": "Dune",
        "author": "Frank Herbert",
        "year": "1965"
    })

    assert book.genre == ""
    assert book.to_dict()["genre"] == ""


def test_storage_saves_and_loads_genre(tmp_path):
    filename = tmp_path / "books.json"
    storage = JSONStorage(filename)
    books = [Book("Dune", "Frank Herbert", "1965", "Science fiction")]

    storage.save_books(books)

    assert storage.load_books()[0].genre == "Science fiction"
    assert json.loads(filename.read_text(encoding="utf-8"))[0]["genre"] == "Science fiction"


def test_storage_loads_legacy_books_without_genre(tmp_path):
    filename = tmp_path / "books.json"
    filename.write_text(
        '[{"title": "Dune", "author": "Frank Herbert", "year": "1965"}]',
        encoding="utf-8"
    )

    books = JSONStorage(filename).load_books()

    assert books[0].genre == ""


def test_filter_books_matches_genre_without_case_sensitivity():
    books = [
        Book("Dune", "Frank Herbert", "1965", "Science fiction"),
        Book("Foundation", "Isaac Asimov", "1951", "science fiction"),
        Book("Emma", "Jane Austen", "1815", "Romance")
    ]

    assert [book.title for book in filter_books(books, " SCIENCE FICTION ")] == [
        "Dune",
        "Foundation"
    ]


def test_filter_books_can_select_books_without_genre():
    books = [
        Book("Dune", "Frank Herbert", "1965", ""),
        Book("Emma", "Jane Austen", "1815", "Romance")
    ]

    assert [book.title for book in filter_books(books, "Без жанра")] == ["Dune"]


def test_filter_books_returns_empty_when_genre_does_not_match():
    books = [Book("Dune", "Frank Herbert", "1965", "Science fiction")]

    assert filter_books(books, "Romance") == []


def test_main_adds_book_and_filters_by_genre(tmp_path, monkeypatch, capsys):
    filename = tmp_path / "books.json"
    monkeypatch.setattr(main, "JSONStorage", lambda: JSONStorage(filename))
    answers = iter([
        "1",
        "The Hobbit",
        "J.R.R. Tolkien",
        "1937",
        "Fantasy",
        "4",
        "fantasy",
        "5"
    ])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))

    main.main()

    output = capsys.readouterr().out
    assert '"The Hobbit" — J.R.R. Tolkien (1937 г.), жанр: Fantasy' in output
    assert JSONStorage(filename).load_books()[0].genre == "Fantasy"
