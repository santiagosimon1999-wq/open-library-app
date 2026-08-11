import requests
import streamlit as st


RESULTS_PER_PAGE = 10


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

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    return response.json()


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


# -------------------------
# Page
# -------------------------

st.title("Open Library Book Search")

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
        st.warning("Please enter something to search.")

    else:
        st.session_state.query = clean_query
        st.session_state.search_by = search_by
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

        books = data.get("docs", [])
        total_results = data.get("numFound", 0)

        if not books:
            st.info("No books found. Try another search.")

        else:
            
            # Scroll back to the top after changing pages
            
            if st.session_state.scroll_to_results:
                current_page = st.session_state.page

                st.html(
                    f"""
                    <div id="results-top-{current_page}"></div>

                    <script>
                        setTimeout(() => {{
                            const target = document.getElementById(
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
                f"— {total_results:,} results found"
            )

            # -------------------------
            # Display books
            # -------------------------

            for book in books:
                title = book.get("title", "Unknown")

                authors = book.get("author_name", [])
                author = authors[0] if authors else "Unknown"

                year = book.get(
                    "first_publish_year",
                    "Unknown"
                )

                cover_id = book.get("cover_i")

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
                        st.write("No cover")

                with col2:
                    st.write(f"Title: {title}")
                    st.write(f"Author: {author}")
                    st.write(f"First Published: {year}")

                st.write("---")


            # -------------------------
            # Pagination
            # -------------------------

            previous_col, next_col = st.columns(2)

            with previous_col:
                if st.button(
                    "← Previous",
                    disabled=st.session_state.page == 1
                ):
                    st.session_state.page -= 1
                    st.session_state.scroll_to_results = True
                    st.rerun()

            with next_col:
                if st.button("Next →"):
                    st.session_state.page += 1
                    st.session_state.scroll_to_results = True
                    st.rerun()


    except requests.exceptions.RequestException:
        st.error(
            "Something went wrong while connecting "
            "to Open Library. Please try again."
        )