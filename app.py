import requests
import streamlit as st

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


RESULTS_PER_PAGE = 10
EDITIONS_TO_SHOW = 5

# Cache API results for 10 minutes
CACHE_TTL = 600

# First number = time allowed to establish the connection
# Second number = time allowed while waiting for data
REQUEST_TIMEOUT = (15, 30)

REQUEST_HEADERS = {
    "User-Agent": (
        "open-library-book-search/1.0 "
        "(learning project)"
    ),
    "Accept": "application/json",
}


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


# =========================================================
# HTTP SESSION
# =========================================================

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
        allowed_methods=frozenset(
            ["GET"]
        ),
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


# =========================================================
# API FUNCTIONS
# =========================================================

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

    return api_get(
        url
    )


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


# =========================================================
# HELPER FUNCTIONS
# =========================================================

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

    return " ".join(
        badges
    )


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

    visible_authors = authors[
        :max_authors
    ]

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


def show_request_error(error):
    if isinstance(
        error,
        requests.exceptions.Timeout
    ):
        st.error(
            "Open Library took too long "
            "to respond after several attempts."
        )

    elif isinstance(
        error,
        requests.exceptions.ConnectionError
    ):
        st.error(
            "A connection error occurred "
            "while contacting Open Library."
        )

    elif isinstance(
        error,
        requests.exceptions.HTTPError
    ):
        st.error(
            "Open Library returned an HTTP error."
        )

    else:
        st.error(
            "Something went wrong while "
            "contacting Open Library."
        )

    st.caption(
        f"Technical error: {error}"
    )


# =========================================================
# SESSION STATE
# =========================================================

if "page" not in st.session_state:
    st.session_state.page = 1

if "query" not in st.session_state:
    st.session_state.query = ""

if "search_by" not in st.session_state:
    st.session_state.search_by = "Title"

if "searched" not in st.session_state:
    st.session_state.searched = False

if "scroll_to_results" not in st.session_state:
    st.session_state.scroll_to_results = False

if "view" not in st.session_state:
    st.session_state.view = "search"

if "selected_book" not in st.session_state:
    st.session_state.selected_book = None

if "scroll_to_details" not in st.session_state:
    st.session_state.scroll_to_details = False

if "load_editions" not in st.session_state:
    st.session_state.load_editions = False


# =========================================================
# BOOK DETAILS VIEW
# =========================================================

if (
    st.session_state.view == "details"
    and st.session_state.selected_book
):

    book = st.session_state.selected_book


    # -------------------------
    # Scroll to top of details
    # -------------------------

    if st.session_state.scroll_to_details:

        st.html(
            """
            <script>
                setTimeout(() => {
                    const main = document.querySelector(
                        'section[data-testid="stMain"]'
                    );

                    if (main) {
                        main.scrollTo({
                            top: 0,
                            behavior: "smooth"
                        });
                    }
                }, 250);
            </script>
            """,
            unsafe_allow_javascript=True,
        )

        st.session_state.scroll_to_details = False


    # -------------------------
    # Back button
    # -------------------------

    if st.button(
        "← Back to Results"
    ):

        st.session_state.view = "search"

        st.session_state.selected_book = None

        st.session_state.load_editions = False

        st.session_state.scroll_to_results = True

        st.rerun()


    work_key = book.get(
        "key"
    )

    if not work_key:

        st.error(
            "This book does not have "
            "an Open Library Work ID."
        )

        st.stop()


    try:

        # -------------------------
        # Work details
        # -------------------------

        with st.spinner(
            "Loading book details..."
        ):

            work_data = get_work_details(
                work_key
            )


        title = book.get(
            "title",
            "Unknown"
        )

        authors = book.get(
            "author_name",
            []
        )

        author = (
            authors[0]
            if authors
            else "Unknown"
        )

        year = book.get(
            "first_publish_year",
            "Unknown"
        )

        edition_count = book.get(
            "edition_count",
            "Unknown"
        )

        cover_id = book.get(
            "cover_i"
        )

        description = get_description(
            work_data
        )

        subjects = work_data.get(
            "subjects",
            []
        )

        availability_details = (
            get_availability_details(
                book
            )
        )


        # =================================================
        # BOOK OVERVIEW
        # =================================================

        with st.container(
            border=True
        ):

            col1, col2 = st.columns(
                [1, 2.4],
                vertical_alignment="center"
            )


            with col1:

                if cover_id:

                    cover_url = (
                        "https://covers.openlibrary.org/"
                        f"b/id/{cover_id}-L.jpg"
                    )

                    st.image(
                        cover_url,
                        width=220
                    )

                else:

                    st.info(
                        "No cover available"
                    )


            with col2:

                st.caption(
                    "BOOK DETAILS"
                )

                st.title(
                    title
                )

                st.write(
                    f"**Author:** {author}"
                )

                st.write("")

                year_col, editions_col = (
                    st.columns(2)
                )


                with year_col:

                    st.metric(
                        "First published",
                        year,
                        border=True
                    )


                with editions_col:

                    st.metric(
                        "Editions",
                        edition_count,
                        border=True
                    )


        st.write("")


        # =================================================
        # DESCRIPTION
        # =================================================

        st.subheader(
            "Description"
        )

        with st.container(
            border=True
        ):

            st.write(
                description
            )


        st.write("")


        # =================================================
        # SUBJECTS
        # =================================================

        st.subheader(
            "Subjects"
        )


        if subjects:

            subject_badges = (
                get_subject_badges(
                    subjects
                )
            )

            st.markdown(
                subject_badges
            )

        else:

            st.info(
                "No subjects available."
            )


        st.write("")


        # =================================================
        # AVAILABILITY
        # =================================================

        st.subheader(
            "Availability"
        )


        with st.container(
            border=True
        ):

            if not availability_details:

                if (
                    book.get("public_scan_b")
                    or book.get("has_fulltext")
                ):

                    st.info(
                        "Digital content exists, "
                        "but detailed availability "
                        "was not returned."
                    )

                else:

                    st.info(
                        "No digital availability "
                        "information found."
                    )


            else:

                availability_status = (
                    availability_details[
                        "status"
                    ]
                )


                if availability_status in [
                    "Open access",
                    "Borrow available",
                ]:

                    st.success(
                        f"Status: "
                        f"{availability_status}"
                    )

                else:

                    st.info(
                        f"Status: "
                        f"{availability_status}"
                    )


                (
                    read_col,
                    preview_col,
                    borrow_col,
                    browse_col,
                ) = st.columns(4)


                with read_col:

                    st.metric(
                        "Read online",
                        yes_or_no(
                            availability_details[
                                "readable"
                            ]
                        ),
                        border=True
                    )


                with preview_col:

                    st.metric(
                        "Preview",
                        yes_or_no(
                            availability_details[
                                "previewable"
                            ]
                        ),
                        border=True
                    )


                with borrow_col:

                    st.metric(
                        "Borrowing",
                        yes_or_no(
                            availability_details[
                                "lendable"
                            ]
                        ),
                        border=True
                    )


                with browse_col:

                    st.metric(
                        "Browse",
                        yes_or_no(
                            availability_details[
                                "browseable"
                            ]
                        ),
                        border=True
                    )


                if availability_details["waitlist"]:

                    st.caption(
                        "Waitlist available"
                    )


                availability_edition = (
                    availability_details[
                        "edition_id"
                    ]
                )


                if availability_edition:

                    availability_edition_id = (
                        availability_edition
                        .rstrip("/")
                        .split("/")[-1]
                    )

                    availability_url = (
                        "https://openlibrary.org/"
                        f"books/"
                        f"{availability_edition_id}"
                    )

                    st.link_button(
                        "Open available edition",
                        availability_url
                    )


        st.write("")


        # =================================================
        # EDITIONS
        # =================================================

        st.subheader(
            "Editions"
        )


        if not st.session_state.load_editions:

            with st.container(
                border=True
            ):

                st.write(
                    "**Want more publication details?**"
                )

                st.caption(
                    "Edition information is loaded "
                    "separately to keep this page fast."
                )

                if st.button(
                    "Load editions",
                    type="primary"
                ):

                    st.session_state.load_editions = True

                    st.rerun()


        else:

            editions = []

            editions_error = None

            try:

                with st.spinner(
                    "Loading editions..."
                ):

                    editions_data = (
                        get_work_editions(
                            work_key
                        )
                    )

                editions = editions_data.get(
                    "entries",
                    []
                )

            except requests.exceptions.RequestException as error:

                editions_error = error


            if editions_error:

                st.warning(
                    "Edition information "
                    "could not be loaded."
                )

                st.caption(
                    f"Technical error: "
                    f"{editions_error}"
                )


            elif not editions:

                st.info(
                    "No edition information available."
                )


            else:

                st.caption(
                    f"Showing up to "
                    f"{EDITIONS_TO_SHOW} editions."
                )


                for edition_number, edition in enumerate(
                    editions,
                    start=1
                ):

                    edition_title = edition.get(
                        "title",
                        title
                    )

                    publish_date = edition.get(
                        "publish_date",
                        "Unknown"
                    )

                    publishers = edition.get(
                        "publishers",
                        []
                    )

                    publisher = (
                        ", ".join(
                            publishers[:2]
                        )
                        if publishers
                        else "Unknown"
                    )

                    pages = edition.get(
                        "number_of_pages",
                        "Unknown"
                    )

                    physical_format = edition.get(
                        "physical_format",
                        "Unknown"
                    )

                    language = (
                        get_edition_language(
                            edition
                        )
                    )

                    isbn = get_edition_isbn(
                        edition
                    )


                    edition_label = (
                        f"Edition {edition_number} "
                        f"— {physical_format} "
                        f"— {publish_date}"
                    )


                    with st.expander(
                        edition_label,
                        expanded=False
                    ):

                        edition_info_col1, (
                            edition_info_col2
                        ) = st.columns(2)


                        with edition_info_col1:

                            st.write(
                                f"**Title:** "
                                f"{edition_title}"
                            )

                            st.write(
                                f"**Publisher:** "
                                f"{publisher}"
                            )

                            st.write(
                                f"**Published:** "
                                f"{publish_date}"
                            )

                            st.write(
                                f"**Format:** "
                                f"{physical_format}"
                            )


                        with edition_info_col2:

                            st.write(
                                f"**Pages:** "
                                f"{pages}"
                            )

                            st.write(
                                f"**Language:** "
                                f"{language}"
                            )

                            st.write(
                                f"**ISBN:** "
                                f"{isbn}"
                            )


                        edition_key = edition.get(
                            "key"
                        )


                        if edition_key:

                            edition_url = (
                                "https://openlibrary.org"
                                f"{edition_key}"
                            )

                            st.link_button(
                                "Open this edition",
                                edition_url
                            )


        # =================================================
        # OPEN LIBRARY LINK
        # =================================================

        st.divider()

        work_id = (
            work_key
            .rstrip("/")
            .split("/")[-1]
        )

        open_library_url = (
            f"https://openlibrary.org/"
            f"works/{work_id}"
        )

        st.caption(
            "Source"
        )

        st.link_button(
            "Open book on Open Library",
            open_library_url
        )


    except requests.exceptions.RequestException as error:

        show_request_error(
            error
        )


    st.stop()


# =========================================================
# SEARCH VIEW
# =========================================================

st.title(
    "Open Library Book Search"
)


# -------------------------
# Search form
# -------------------------

with st.form(
    "search_form"
):

    search_options = [
        "Title",
        "Author",
        "ISBN",
    ]

    current_search_index = (
        search_options.index(
            st.session_state.search_by
        )
    )

    search_by = st.selectbox(
        "Search by",
        search_options,
        index=current_search_index,
    )

    query = st.text_input(
        "Search",
        value=st.session_state.query,
        placeholder=(
            "Enter a book title, "
            "author, or ISBN"
        ),
    )

    search_submitted = (
        st.form_submit_button(
            "Search"
        )
    )


# -------------------------
# Process search
# -------------------------

if search_submitted:

    clean_query = query.strip()


    if not clean_query:

        st.warning(
            "Please enter something "
            "to search."
        )


    else:

        search_is_valid = True


        # -------------------------
        # ISBN cleanup / validation
        # -------------------------

        if search_by == "ISBN":

            clean_query = normalize_isbn(
                clean_query
            )

            if not is_valid_isbn_format(
                clean_query
            ):

                st.warning(
                    "Please enter a valid "
                    "ISBN-10 or ISBN-13."
                )

                search_is_valid = False


        # -------------------------
        # Save valid search
        # -------------------------

        if search_is_valid:

            st.session_state.query = (
                clean_query
            )

            st.session_state.search_by = (
                search_by
            )

            st.session_state.page = 1

            st.session_state.searched = True

            st.session_state.scroll_to_results = True


# -------------------------
# Search results
# -------------------------

if st.session_state.searched:

    try:

        with st.spinner(
            "Searching Open Library..."
        ):

            data = searchbooks(
                st.session_state.query,
                st.session_state.search_by,
                st.session_state.page,
            )


        books = data.get(
            "docs",
            []
        )

        total_results = data.get(
            "numFound",
            data.get(
                "num_found",
                0
            )
        )

        total_pages = max(
            1,
            (
                total_results
                + RESULTS_PER_PAGE
                - 1
            )
            // RESULTS_PER_PAGE
        )


        # -------------------------
        # Results heading
        # -------------------------

        st.subheader(
            f'Results for '
            f'"{st.session_state.query}"'
        )

        st.caption(
            f"Searching by "
            f"{st.session_state.search_by}"
        )


        if not books:

            st.info(
                "No books found. "
                "Try another search."
            )


        else:

            # -------------------------
            # Scroll to results
            # -------------------------

            if st.session_state.scroll_to_results:

                current_page = (
                    st.session_state.page
                )

                st.html(
                    f"""
                    <div id="results-top-{current_page}"></div>

                    <script>
                        setTimeout(() => {{
                            const target =
                                document.getElementById(
                                    "results-top-{current_page}"
                                );

                            if (target) {{
                                target.scrollIntoView({{
                                    behavior: "smooth",
                                    block: "start"
                                }});
                            }}
                        }}, 250);
                    </script>
                    """,
                    unsafe_allow_javascript=True,
                )

                st.session_state.scroll_to_results = False


            st.write(
                f"Page {st.session_state.page} "
                f"of {total_pages} "
                f"— {total_results:,} "
                f"results found"
            )


            # =================================================
            # DISPLAY BOOK CARDS
            # =================================================

            for index, book in enumerate(
                books
            ):

                title = book.get(
                    "title",
                    "Unknown"
                )

                authors_text = (
                    get_authors_text(
                        book
                    )
                )

                year = book.get(
                    "first_publish_year",
                    "Unknown"
                )

                edition_count = book.get(
                    "edition_count",
                    "Unknown"
                )

                cover_id = book.get(
                    "cover_i"
                )


                with st.container(
                    border=True
                ):

                    cover_col, info_col = (
                        st.columns(
                            [1, 3.5],
                            vertical_alignment="center"
                        )
                    )


                    # -------------------------
                    # Cover
                    # -------------------------

                    with cover_col:

                        if cover_id:

                            cover_url = (
                                "https://covers.openlibrary.org/"
                                f"b/id/{cover_id}-M.jpg"
                            )

                            st.image(
                                cover_url,
                                width=120
                            )

                        else:

                            st.info(
                                "No cover"
                            )


                    # -------------------------
                    # Book information
                    # -------------------------

                    with info_col:

                        st.markdown(
                            f"### {title}"
                        )

                        st.write(
                            f"**Author(s):** "
                            f"{authors_text}"
                        )

                        metadata_col1, (
                            metadata_col2
                        ) = st.columns(2)


                        with metadata_col1:

                            st.metric(
                                "First published",
                                year,
                                border=True
                            )


                        with metadata_col2:

                            st.metric(
                                "Editions",
                                edition_count,
                                border=True
                            )


                        if st.button(
                            "View Details",
                            key=(
                                f"details_"
                                f"{st.session_state.page}_"
                                f"{index}"
                            ),
                            type="primary"
                        ):

                            st.session_state.selected_book = book

                            st.session_state.view = "details"

                            st.session_state.load_editions = False

                            st.session_state.scroll_to_details = True

                            st.rerun()


                st.write("")


            # -------------------------
            # Pagination
            # -------------------------

            previous_col, next_col = st.columns(
                2
            )


            with previous_col:

                if st.button(
                    "← Previous",
                    disabled=(
                        st.session_state.page <= 1
                    )
                ):

                    st.session_state.page -= 1

                    st.session_state.scroll_to_results = True

                    st.rerun()


            with next_col:

                if st.button(
                    "Next →",
                    disabled=(
                        st.session_state.page
                        >= total_pages
                    )
                ):

                    st.session_state.page += 1

                    st.session_state.scroll_to_results = True

                    st.rerun()


    except requests.exceptions.RequestException as error:

        show_request_error(
            error
        )