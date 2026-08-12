import requests
import streamlit as st


RESULTS_PER_PAGE = 10
EDITIONS_TO_SHOW = 5


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


# -------------------------
# API functions
# -------------------------

def searchbooks(query, search_by, page):
    url = "https://openlibrary.org/search.json"

    if search_by == "Title":
        params = {
            "title": query,
            "limit": RESULTS_PER_PAGE,
            "page": page,
        }
    else:
        params = {
            "author": query,
            "limit": RESULTS_PER_PAGE,
            "page": page,
        }

    params["fields"] = (
        "key,title,author_name,first_publish_year,"
        "cover_i,edition_count,has_fulltext,"
        "public_scan_b,ia,availability"
    )

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    return response.json()


def get_work_details(work_key):
    work_id = work_key.rstrip("/").split("/")[-1]

    url = f"https://openlibrary.org/works/{work_id}.json"

    response = requests.get(
        url,
        timeout=10
    )

    response.raise_for_status()

    return response.json()


def get_work_editions(work_key, limit=EDITIONS_TO_SHOW):
    work_id = work_key.rstrip("/").split("/")[-1]

    url = (
        f"https://openlibrary.org/works/"
        f"{work_id}/editions.json"
    )

    params = {
        "limit": limit
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    return response.json()


def get_description(work_data):
    description = work_data.get("description")

    if isinstance(description, dict):
        return description.get(
            "value",
            "No description available."
        )

    if isinstance(description, str):
        return description

    return "No description available."


def get_availability_text(book):
    availability = book.get("availability") or {}

    if availability.get("is_readable"):
        return "Readable online"

    if availability.get("is_lendable"):
        return "Available to borrow"

    if availability.get("status") == "open":
        return "Open access"

    if book.get("public_scan_b"):
        return "Public scan available"

    if book.get("has_fulltext"):
        return "Full text available"

    return "No digital availability found."


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
        return ", ".join(language_names)

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


# -------------------------
# Session state
# -------------------------

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

    if st.button("← Back to Results"):
        st.session_state.view = "search"
        st.session_state.selected_book = None
        st.session_state.scroll_to_results = True
        st.rerun()


    work_key = book.get("key")

    if not work_key:
        st.error(
            "This book does not have an Open Library Work ID."
        )
        st.stop()


    try:

        # -------------------------
        # Work details
        # -------------------------

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

        availability_text = get_availability_text(
            book
        )


        # -------------------------
        # Editions data
        # -------------------------

        editions = []
        editions_error = False

        try:
            editions_data = get_work_editions(
                work_key
            )

            editions = editions_data.get(
                "entries",
                []
            )

        except requests.exceptions.RequestException:
            editions_error = True


        # -------------------------
        # Main book information
        # -------------------------

        col1, col2 = st.columns(
            [1, 2],
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
                st.write(
                    "No cover available"
                )


        with col2:

            st.title(
                title
            )

            st.write(
                f"**Author:** {author}"
            )

            st.write(
                f"**First Published:** {year}"
            )

            st.write(
                f"**Editions:** {edition_count}"
            )


        st.divider()


        # -------------------------
        # Description
        # -------------------------

        st.subheader(
            "Description"
        )

        st.write(
            description
        )


        # -------------------------
        # Subjects
        # -------------------------

        st.subheader(
            "Subjects"
        )

        if subjects:

            st.write(
                ", ".join(
                    subjects[:12]
                )
            )

        else:

            st.write(
                "No subjects available."
            )


        # -------------------------
        # Availability
        # -------------------------

        st.subheader(
            "Availability"
        )

        if (
            availability_text
            == "No digital availability found."
        ):

            st.info(
                availability_text
            )

        else:

            st.success(
                availability_text
            )


        # -------------------------
        # Editions
        # -------------------------

        st.subheader(
            "Editions"
        )

        if editions_error:

            st.warning(
                "Edition information could not be loaded."
            )

        elif not editions:

            st.info(
                "No edition information available."
            )

        else:

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

                language = get_edition_language(
                    edition
                )

                isbn = get_edition_isbn(
                    edition
                )


                # -------------------------
                # Compact edition header
                # -------------------------

                edition_label = (
                    f"Edition {edition_number} "
                    f"— {physical_format} "
                    f"— {publish_date}"
                )


                # -------------------------
                # Expandable edition
                # -------------------------

                with st.expander(
                    edition_label,
                    expanded=False
                ):

                    st.write(
                        f"**Title:** {edition_title}"
                    )

                    st.write(
                        f"**Published:** {publish_date}"
                    )

                    st.write(
                        f"**Publisher:** {publisher}"
                    )

                    st.write(
                        f"**Format:** {physical_format}"
                    )

                    st.write(
                        f"**Pages:** {pages}"
                    )

                    st.write(
                        f"**Language:** {language}"
                    )

                    st.write(
                        f"**ISBN:** {isbn}"
                    )


                    # -------------------------
                    # Edition link
                    # -------------------------

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


        # -------------------------
        # Open Library work link
        # -------------------------

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

        st.link_button(
            "Open in Open Library",
            open_library_url
        )


    except requests.exceptions.RequestException:

        st.error(
            "Something went wrong while loading "
            "the book details."
        )


    st.stop()


# =========================================================
# SEARCH VIEW
# =========================================================

st.title(
    "Open Library Book Search"
)


search_by = st.selectbox(
    "Search by",
    ["Title", "Author"]
)


query = st.text_input(
    "Search",
    placeholder="Enter a book title or author"
)


# -------------------------
# Search button
# -------------------------

if st.button("Search"):

    clean_query = query.strip()

    if not clean_query:

        st.warning(
            "Please enter something to search."
        )

    else:

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
                f"— {total_results:,} results found"
            )


            # -------------------------
            # Display books
            # -------------------------

            for index, book in enumerate(
                books
            ):

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

                cover_id = book.get(
                    "cover_i"
                )


                col1, col2 = st.columns(
                    [1, 3],
                    vertical_alignment="center"
                )


                with col1:

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

                        st.write(
                            "No cover"
                        )


                with col2:

                    st.write(
                        f"**Title:** {title}"
                    )

                    st.write(
                        f"**Author:** {author}"
                    )

                    st.write(
                        f"**First Published:** {year}"
                    )


                    # -------------------------
                    # View Details
                    # -------------------------

                    if st.button(
                        "View Details",
                        key=(
                            f"details_"
                            f"{st.session_state.page}_"
                            f"{index}"
                        )
                    ):

                        st.session_state.selected_book = book

                        st.session_state.view = "details"

                        st.session_state.scroll_to_details = True

                        st.rerun()


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


    except requests.exceptions.RequestException:

        st.error(
            "Something went wrong while connecting "
            "to Open Library. Please try again."
        )