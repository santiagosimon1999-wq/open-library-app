LANGUAGE_NAMES = {
    "eng": "English",
    "spa": "Spanish",
    "fre": "French",
    "fra": "French",
    "ger": "German",
    "deu": "German",
    "ita": "Italian",
    "por": "Portuguese",
    "rus": "Russian",
    "jpn": "Japanese",
    "chi": "Chinese",
    "zho": "Chinese",
    "kor": "Korean",
    "ara": "Arabic",
    "dut": "Dutch",
    "nld": "Dutch",
    "pol": "Polish",
    "swe": "Swedish",
    "nor": "Norwegian",
    "dan": "Danish",
    "fin": "Finnish",
    "cze": "Czech",
    "ces": "Czech",
    "hun": "Hungarian",
    "tur": "Turkish",
    "heb": "Hebrew",
    "gre": "Greek",
    "ell": "Greek",
    "lat": "Latin",
}


AVAILABILITY_STATUS_NAMES = {
    "open": "Open access",
    "borrow_available": "Borrow available",
    "borrow_unavailable": "Borrow unavailable",
}


def get_description(work_data):
    description = work_data.get(
        "description"
    )

    if isinstance(description, dict):
        return description.get(
            "value",
            "No description available."
        )

    if isinstance(description, str):
        return description

    return "No description available."


def normalize_isbn(isbn):
    return (
        isbn
        .replace("-", "")
        .replace(" ", "")
        .upper()
    )


def is_valid_isbn_format(isbn):
    if len(isbn) == 13:
        return isbn.isdigit()

    if len(isbn) == 10:
        return (
            isbn[:9].isdigit()
            and (
                isbn[-1].isdigit()
                or isbn[-1] == "X"
            )
        )

    return False


def get_availability_details(book):
    availability = book.get(
        "availability"
    ) or {}

    if not availability:
        return None

    status_code = availability.get(
        "status",
        "unknown"
    )

    status_name = AVAILABILITY_STATUS_NAMES.get(
        status_code,
        status_code.replace(
            "_",
            " "
        ).title()
    )

    readable = bool(
        availability.get(
            "is_readable"
        )
    )
    lendable = bool(
        availability.get(
            "is_lendable"
        )
    )
    previewable = bool(
        availability.get(
            "is_previewable"
        )
    )
    browseable = bool(
        availability.get(
            "available_to_browse"
        )
        or availability.get(
            "is_browseable"
        )
    )
    waitlist = bool(
        availability.get(
            "available_to_waitlist"
        )
    )
    edition_id = availability.get(
        "openlibrary_edition"
    )

    return {
        "status": status_name,
        "readable": readable,
        "lendable": lendable,
        "previewable": previewable,
        "browseable": browseable,
        "waitlist": waitlist,
        "edition_id": edition_id,
    }


def yes_or_no(value):
    if value:
        return "Yes"
    return "No"


def get_subject_badges(subjects):
    badges = []

    for subject in subjects[:12]:
        safe_subject = (
            str(subject)
            .replace("[", "(")
            .replace("]", ")")
        )

        badges.append(
            f":blue-badge[{safe_subject}]"
        )

    return " ".join(badges)


def get_authors_text(
    book,
    max_authors=3
):
    authors = book.get(
        "author_name",
        []
    )

    if not authors:
        return "Unknown"

    visible_authors = authors[:max_authors]
    authors_text = ", ".join(
        visible_authors
    )

    remaining_authors = (
        len(authors)
        - len(visible_authors)
    )

    if remaining_authors > 0:
        authors_text += (
            f" + {remaining_authors} more"
        )

    return authors_text


def get_book_key(book):
    book_key = book.get(
        "key"
    )

    if book_key:
        return book_key

    title = book.get(
        "title",
        "Unknown"
    )
    authors = book.get(
        "author_name",
        []
    )
    authors_text = "|".join(
        authors
    )

    return f"{title}|{authors_text}"


def is_book_saved(
    book,
    saved_books
):
    book_key = get_book_key(book)

    for saved_book in saved_books:
        if get_book_key(
            saved_book
        ) == book_key:
            return True

    return False


def save_book(
    book,
    saved_books
):
    if is_book_saved(
        book,
        saved_books
    ):
        return saved_books

    return [
        *saved_books,
        book,
    ]


def remove_saved_book(
    book,
    saved_books
):
    book_key = get_book_key(book)

    return [
        saved_book
        for saved_book in saved_books
        if get_book_key(
            saved_book
        ) != book_key
    ]


def get_edition_language(edition):
    languages = edition.get(
        "languages",
        []
    )

    language_names = []

    for language in languages:
        if isinstance(language, dict):
            language_key = language.get(
                "key",
                ""
            )

            if language_key:
                language_code = (
                    language_key
                    .split("/")[-1]
                    .lower()
                )

                language_name = LANGUAGE_NAMES.get(
                    language_code,
                    language_code.upper()
                )

                language_names.append(
                    language_name
                )

    if language_names:
        return ", ".join(
            language_names
        )

    return "Unknown"


def get_edition_isbn(edition):
    isbns = (
        edition.get("isbn_13")
        or edition.get("isbn_10")
        or []
    )

    if isbns:
        return isbns[0]

    return "Unknown"
