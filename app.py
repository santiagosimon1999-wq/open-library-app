import requests
import streamlit as st


def searchbooks(query):
    url = "https://openlibrary.org/search.json"

    params = {
        "q": query,
        "limit": 10
    }

    response = requests.get(url, params=params)

    return response.json()

st.title("Open Library Book Search")

query = st.text_input("Search for a book")

if st.button("Search"):
    if query:
        data = searchbooks(query)

        for book in data.get("docs", []):
            title = book.get("title", "Unknown")

            authors = book.get("author_name", [])
            author = authors[0] if authors else "Unknown"

            year = book.get("first_publish_year", "Unknown")

            cover_id = book.get("cover_i")

            col1, col2 = st.columns([1, 3])

            with col1:
                if cover_id:
                    cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
                    st.image(cover_url, width=120)
                else:
                    st.write("No cover")

                with col2:
                    st.write(f"Title: {title}")
                    st.write(f"Author: {author}")
                    st.write(f"First Published: {year}")

                    st.write("---")