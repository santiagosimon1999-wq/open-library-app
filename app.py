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

st.write("My first Streamlit application!")

query = st.text_input("Search for a book")

if st.button("Search"):
    if query:
        data = searchbooks(query)

        for book in data.get("docs", []):
            st.write(f"Title: {book.get('title', 'N/A')}")
            st.write(f"Author: {book.get('author_name', ['N/A'])[0]}")
            st.write(f"Year: {book.get('first_publish_year', 'N/A')}")
            st.write("---")
