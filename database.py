import streamlit as st

from supabase import Client, create_client


# =========================================================
# SUPABASE CLIENT
# =========================================================


def get_supabase_client():
    """
    Return one Supabase client for the current Streamlit session.

    Authentication belongs to one visitor session, so the client is
    stored in st.session_state instead of a global shared cache.
    """

    if "supabase_client" not in st.session_state:
        url = st.secrets[
            "SUPABASE_URL"
        ]

        key = st.secrets[
            "SUPABASE_PUBLISHABLE_KEY"
        ]

        st.session_state.supabase_client = create_client(
            url,
            key
        )

    return st.session_state.supabase_client


# =========================================================
# AUTH
# =========================================================


def user_to_dict(user):
    if not user:
        return None

    return {
        "id": str(user.id),
        "email": user.email,
    }


def get_current_user():
    return st.session_state.get(
        "auth_user"
    )


def sign_up(email, password):
    supabase = get_supabase_client()

    response = supabase.auth.sign_up(
        {
            "email": email,
            "password": password,
        }
    )

    # When email confirmation is disabled, Supabase can return
    # a session immediately. In that case the user is signed in.
    if response.session and response.user:
        st.session_state.auth_user = (
            user_to_dict(
                response.user
            )
        )

    return response


def sign_in(email, password):
    supabase = get_supabase_client()

    response = (
        supabase.auth.sign_in_with_password(
            {
                "email": email,
                "password": password,
            }
        )
    )

    if response.user:
        st.session_state.auth_user = (
            user_to_dict(
                response.user
            )
        )

    return response


def sign_out():
    supabase = get_supabase_client()

    supabase.auth.sign_out()

    st.session_state.auth_user = None


# =========================================================
# SAVED BOOKS
# =========================================================


def _integer_or_none(value):
    if isinstance(value, int):
        return value

    return None


def _database_row_to_book(row):
    book_data = row.get(
        "book_data"
    )

    if isinstance(book_data, dict):
        return book_data

    # Fallback for older rows if book_data is ever missing.
    return {
        "key": row.get("work_key"),
        "title": row.get(
            "title",
            "Unknown"
        ),
        "author_name": row.get(
            "authors",
            []
        ) or [],
        "first_publish_year": row.get(
            "first_publish_year"
        ),
        "cover_i": row.get(
            "cover_id"
        ),
        "edition_count": row.get(
            "edition_count"
        ),
    }


def load_saved_books(user_id):
    supabase = get_supabase_client()

    response = (
        supabase
        .table("saved_books")
        .select(
            "work_key,title,authors,"
            "first_publish_year,cover_id,"
            "edition_count,book_data,created_at"
        )
        .eq(
            "user_id",
            user_id
        )
        .order(
            "created_at",
            desc=True
        )
        .execute()
    )

    rows = response.data or []

    return [
        _database_row_to_book(row)
        for row in rows
    ]


def save_book_to_database(
    user_id,
    book
):
    supabase = get_supabase_client()

    work_key = book.get(
        "key"
    )

    if not work_key:
        raise ValueError(
            "This book does not have an Open Library Work ID."
        )

    authors = book.get(
        "author_name",
        []
    )

    if not isinstance(authors, list):
        authors = []

    payload = {
        "user_id": user_id,
        "work_key": work_key,
        "title": book.get(
            "title",
            "Unknown"
        ),
        "authors": authors,
        "first_publish_year": _integer_or_none(
            book.get(
                "first_publish_year"
            )
        ),
        "cover_id": _integer_or_none(
            book.get(
                "cover_i"
            )
        ),
        "edition_count": _integer_or_none(
            book.get(
                "edition_count"
            )
        ),
        "book_data": book,
    }

    return (
        supabase
        .table("saved_books")
        .insert(
            payload
        )
        .execute()
    )


def remove_book_from_database(
    user_id,
    book
):
    supabase = get_supabase_client()

    work_key = book.get(
        "key"
    )

    if not work_key:
        raise ValueError(
            "This book does not have an Open Library Work ID."
        )

    return (
        supabase
        .table("saved_books")
        .delete()
        .eq(
            "user_id",
            user_id
        )
        .eq(
            "work_key",
            work_key
        )
        .execute()
    )
