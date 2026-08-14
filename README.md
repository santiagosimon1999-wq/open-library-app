# Open Library Book Search

A full-stack book discovery app built with **Python**, **Streamlit**, **Open Library**, and **Supabase**.

Users can search for books by title, author, or ISBN, inspect detailed book information and editions, create an account, and save favorite books permanently to their personal library.

## Features

- Search books by **Title**, **Author**, or **ISBN**
- Paginated Open Library search results
- Book covers, authors, publication year, and edition counts
- Detailed book pages with:
  - Description
  - Subject tags
  - Availability information
  - Lazy-loaded edition data
  - Publisher, format, page count, language, and ISBN details
- Open Library links for books and editions
- Account registration with email confirmation
- Login and logout with Supabase Auth
- Persistent Saved Books tied to each user account
- Row Level Security so users can only access their own saved books
- Cached API responses for faster repeated searches
- HTTP retry and error-handling logic for unreliable API responses
- Responsive Streamlit interface with sidebar navigation
- Automated tests with pytest

## Tech Stack

| Area | Technology |
| --- | --- |
| Language | Python |
| UI | Streamlit |
| Book API | Open Library API |
| Authentication | Supabase Auth |
| Database | Supabase PostgreSQL |
| Security | Supabase Row Level Security |
| HTTP | Requests / urllib3 |
| Testing | pytest |
| Version Control | Git / GitHub |

## Architecture

The project uses a modular monolith structure. The application runs as one service, while responsibilities are separated into Python modules.

```text
open-library-app/
├── app.py                 # Streamlit UI, navigation, auth flow, views
├── api.py                 # Open Library API requests, caching, retries
├── database.py            # Supabase auth and persistent saved books
├── helpers.py             # Formatting, ISBN and utility functions
├── tests/
│   ├── test_helpers.py
│   └── test_database_helpers.py
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

### Application flow

```text
User
  ↓
Streamlit UI
  ├── Open Library API
  │     └── Search / Work details / Editions
  │
  └── Supabase
        ├── Authentication
        └── PostgreSQL saved_books
              └── Row Level Security by user_id
```

## Authentication and Database

Supabase Auth manages user accounts and email confirmation.

Saved books are stored in PostgreSQL and associated with the authenticated user's UUID.

The `saved_books` table includes information such as:

```text
user_id
work_key
title
authors
first_publish_year
cover_id
edition_count
book_data
created_at
```

Row Level Security policies restrict SELECT, INSERT, and DELETE operations so authenticated users can only access their own rows.

## Reliability and Performance

The Open Library API can occasionally respond slowly, so the app includes:

- Connection and read timeouts
- Automatic retries with exponential backoff
- Retry handling for HTTP 429 and common 5xx responses
- Streamlit caching for repeated API requests
- Lazy loading for edition information

This keeps the main book details page responsive without requesting every piece of data immediately.

## Automated Tests

The project currently includes **24 automated tests** covering helper and database utility behavior.

Run them with:

```bash
python -m pytest -q
```

Expected result:

```text
24 passed
```

Development dependencies are kept separately in `requirements-dev.txt`.

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/santiagosimon1999-wq/open-library-app.git
cd open-library-app
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

For development and tests:

```bash
pip install -r requirements-dev.txt
```

### 4. Configure Supabase secrets

Create:

```text
.streamlit/secrets.toml
```

Add:

```toml
SUPABASE_URL = "your-project-url"
SUPABASE_PUBLISHABLE_KEY = "your-publishable-key"
```

`secrets.toml` is intentionally excluded from Git.

### 5. Run the application

```bash
streamlit run app.py
```

## Screenshots

Screenshots will be added alongside the public deployment so the README reflects the final production UI.

## What I Practiced

This project was built to practice and apply:

- Working with third-party REST APIs
- Parsing JSON responses
- Python functions and modular project structure
- Streamlit state and rerun behavior
- API caching and lazy loading
- Defensive networking and error handling
- Authentication flows
- PostgreSQL-backed persistent data
- Row Level Security
- Separating UI, API, database, and helper responsibilities
- Automated testing with pytest
- Git and GitHub workflow

## Next Step

The next milestone is deploying the application publicly so it can be accessed from a shareable URL.

---

Built by **Snt** as a portfolio and learning project.
