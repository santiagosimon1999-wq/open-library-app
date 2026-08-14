from helpers import (
    get_authors_text,
    get_book_key,
    get_description,
    get_edition_isbn,
    get_edition_language,
    is_book_saved,
    is_valid_isbn_format,
    normalize_isbn,
    remove_saved_book,
    save_book,
    yes_or_no,
)


def test_normalize_isbn_removes_hyphens_and_spaces():
    assert normalize_isbn(
        "978-0-441-17271-9"
    ) == "9780441172719"


def test_normalize_isbn_uppercases_x():
    assert normalize_isbn(
        "0-8044-2957-x"
    ) == "080442957X"


def test_valid_isbn_13_format():
    assert is_valid_isbn_format(
        "9780441172719"
    )


def test_invalid_isbn_13_with_letters():
    assert not is_valid_isbn_format(
        "978044117271X"
    )


def test_valid_isbn_10_with_x():
    assert is_valid_isbn_format(
        "080442957X"
    )


def test_invalid_isbn_wrong_length():
    assert not is_valid_isbn_format(
        "12345"
    )


def test_get_description_from_string():
    work_data = {
        "description": "A test description."
    }

    assert get_description(
        work_data
    ) == "A test description."


def test_get_description_from_dict():
    work_data = {
        "description": {
            "value": "A dictionary description."
        }
    }

    assert get_description(
        work_data
    ) == "A dictionary description."


def test_get_description_missing():
    assert get_description(
        {}
    ) == "No description available."


def test_get_authors_text_single_author():
    book = {
        "author_name": [
            "Frank Herbert"
        ]
    }

    assert get_authors_text(
        book
    ) == "Frank Herbert"


def test_get_authors_text_multiple_authors():
    book = {
        "author_name": [
            "Author One",
            "Author Two",
            "Author Three",
            "Author Four",
        ]
    }

    assert get_authors_text(
        book,
        max_authors=3
    ) == (
        "Author One, Author Two, "
        "Author Three + 1 more"
    )


def test_get_authors_text_missing():
    assert get_authors_text(
        {}
    ) == "Unknown"


def test_get_book_key_prefers_open_library_key():
    book = {
        "key": "/works/OL123W",
        "title": "Example",
    }

    assert get_book_key(
        book
    ) == "/works/OL123W"


def test_get_book_key_fallback():
    book = {
        "title": "Example",
        "author_name": [
            "Author One",
            "Author Two",
        ],
    }

    assert get_book_key(
        book
    ) == (
        "Example|Author One|Author Two"
    )


def test_saved_book_helpers():
    dune = {
        "key": "/works/OL893415W",
        "title": "Dune",
    }

    books = []

    assert not is_book_saved(
        dune,
        books
    )

    books = save_book(
        dune,
        books
    )

    assert is_book_saved(
        dune,
        books
    )

    duplicate_attempt = save_book(
        dune,
        books
    )

    assert len(
        duplicate_attempt
    ) == 1

    books = remove_saved_book(
        dune,
        books
    )

    assert not is_book_saved(
        dune,
        books
    )


def test_yes_or_no():
    assert yes_or_no(
        True
    ) == "Yes"

    assert yes_or_no(
        False
    ) == "No"


def test_get_edition_language_known_code():
    edition = {
        "languages": [
            {
                "key": "/languages/eng"
            }
        ]
    }

    assert get_edition_language(
        edition
    ) == "English"


def test_get_edition_language_unknown_code():
    edition = {
        "languages": [
            {
                "key": "/languages/xyz"
            }
        ]
    }

    assert get_edition_language(
        edition
    ) == "XYZ"


def test_get_edition_isbn_prefers_isbn_13():
    edition = {
        "isbn_13": [
            "9780441172719"
        ],
        "isbn_10": [
            "0441172717"
        ],
    }

    assert get_edition_isbn(
        edition
    ) == "9780441172719"


def test_get_edition_isbn_unknown():
    assert get_edition_isbn(
        {}
    ) == "Unknown"
