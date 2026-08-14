from database import (
    _database_row_to_book,
    _integer_or_none,
)


def test_integer_or_none_accepts_integer():
    assert _integer_or_none(
        42
    ) == 42


def test_integer_or_none_rejects_string():
    assert _integer_or_none(
        "42"
    ) is None


def test_database_row_to_book_uses_book_data():
    book_data = {
        "key": "/works/OL123W",
        "title": "Example Book",
        "author_name": [
            "Example Author"
        ],
    }

    row = {
        "book_data": book_data
    }

    assert _database_row_to_book(
        row
    ) == book_data


def test_database_row_to_book_fallback():
    row = {
        "book_data": None,
        "work_key": "/works/OL456W",
        "title": "Fallback Book",
        "authors": [
            "Fallback Author"
        ],
        "first_publish_year": 2001,
        "cover_id": 123,
        "edition_count": 7,
    }

    book = _database_row_to_book(
        row
    )

    assert book["key"] == "/works/OL456W"
    assert book["title"] == "Fallback Book"
    assert book["author_name"] == [
        "Fallback Author"
    ]
    assert book["first_publish_year"] == 2001
    assert book["cover_i"] == 123
    assert book["edition_count"] == 7
