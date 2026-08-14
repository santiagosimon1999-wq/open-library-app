import requests
import streamlit as st

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


RESULTS_PER_PAGE = 10
EDITIONS_TO_SHOW = 5
CACHE_TTL = 600
REQUEST_TIMEOUT = (15, 30)

REQUEST_HEADERS = {
    "User-Agent": (
        "open-library-book-search/1.0 "
        "(learning project)"
    ),
    "Accept": "application/json",
}


def create_http_session():
    retry_strategy = Retry(
        total=2,
        connect=2,
        read=2,
        status=2,
        backoff_factor=1,
        status_forcelist=[
            429,
            500,
            502,
            503,
            504,
        ],
        allowed_methods=frozenset(["GET"]),
        respect_retry_after_header=True,
    )

    adapter = HTTPAdapter(
        max_retries=retry_strategy
    )

    session = requests.Session()
    session.headers.update(
        REQUEST_HEADERS
    )
    session.mount(
        "https://",
        adapter
    )
    session.mount(
        "http://",
        adapter
    )

    return session


HTTP_SESSION = create_http_session()


def api_get(url, params=None):
    response = HTTP_SESSION.get(
        url,
        params=params,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(
    ttl=CACHE_TTL,
    show_spinner=False
)
def searchbooks(
    query,
    search_by,
    page
):
    url = "https://openlibrary.org/search.json"

    if search_by == "Title":
        params = {
            "title": query,
            "limit": RESULTS_PER_PAGE,
            "page": page,
        }
    elif search_by == "Author":
        params = {
            "author": query,
            "limit": RESULTS_PER_PAGE,
            "page": page,
        }
    else:
        params = {
            "q": f"isbn:{query}",
            "limit": RESULTS_PER_PAGE,
            "page": page,
        }

    params["fields"] = (
        "key,title,author_name,first_publish_year,"
        "cover_i,edition_count,has_fulltext,"
        "public_scan_b,ia,availability"
    )

    return api_get(
        url,
        params=params,
    )


@st.cache_data(
    ttl=CACHE_TTL,
    show_spinner=False
)
def get_work_details(work_key):
    work_id = (
        work_key
        .rstrip("/")
        .split("/")[-1]
    )

    url = (
        f"https://openlibrary.org/"
        f"works/{work_id}.json"
    )

    return api_get(url)


@st.cache_data(
    ttl=CACHE_TTL,
    show_spinner=False
)
def get_work_editions(
    work_key,
    limit=EDITIONS_TO_SHOW
):
    work_id = (
        work_key
        .rstrip("/")
        .split("/")[-1]
    )

    url = (
        f"https://openlibrary.org/works/"
        f"{work_id}/editions.json"
    )

    params = {
        "limit": limit
    }

    return api_get(
        url,
        params=params,
    )
