import requests
import streamlit as st

from api import (
    EDITIONS_TO_SHOW,
    RESULTS_PER_PAGE,
    get_work_details,
    get_work_editions,
    searchbooks,
)
from database import (
    get_current_user,
    load_saved_books,
    remove_book_from_database,
    save_book_to_database,
    sign_in,
    sign_out,
    sign_up,
)
from helpers import (
    get_authors_text,
    get_availability_details,
    get_description,
    get_edition_isbn,
    get_edition_language,
    get_subject_badges,
    is_book_saved,
    is_valid_isbn_format,
    normalize_isbn,
    yes_or_no,
)


# =========================================================
# UI ERROR HANDLING
# =========================================================


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


def open_login(return_view="search"):
    st.session_state.auth_return_view = (
        return_view
    )
    st.session_state.view = "login"
    st.rerun()


def sync_saved_books():
    user = get_current_user()

    if not user:
        st.session_state.saved_books = []
        return

    st.session_state.saved_books = (
        load_saved_books(
            user["id"]
        )
    )


def set_flash(message, icon="✅"):
    st.session_state.flash_message = {
        "message": message,
        "icon": icon,
    }


def show_flash():
    flash = st.session_state.get(
        "flash_message"
    )

    if not flash:
        return

    st.toast(
        flash["message"],
        icon=flash["icon"],
    )

    st.session_state.flash_message = None


def friendly_auth_error(error, action):
    error_code = str(
        getattr(error, "code", "")
    ).lower()

    error_text = str(error).lower()
    combined_error = (
        f"{error_code} {error_text}"
    )

    if (
        "invalid_credentials" in combined_error
        or "invalid login credentials" in combined_error
    ):
        return (
            "The email or password is incorrect."
        )

    if "email_not_confirmed" in combined_error:
        return (
            "Please confirm your email before logging in."
        )

    if (
        "user_already_exists" in combined_error
        or "user already registered" in combined_error
    ):
        return (
            "An account already exists for this email. "
            "Try logging in instead."
        )

    if "weak_password" in combined_error:
        return (
            "That password does not meet the current "
            "password requirements."
        )

    if (
        "over_email_send_rate_limit" in combined_error
        or "rate limit" in combined_error
    ):
        return (
            "Too many attempts were made recently. "
            "Please wait a little and try again."
        )

    if "signup_disabled" in combined_error:
        return (
            "New account registration is currently unavailable."
        )

    if action == "login":
        return (
            "We could not sign you in. "
            "Please check your information and try again."
        )

    return (
        "We could not create the account. "
        "Please check your information and try again."
    )


def show_saved_book_error(action):
    if action == "save":
        st.error(
            "This book could not be saved right now."
        )
    else:
        st.error(
            "This book could not be removed right now."
        )

    st.caption(
        "Your Saved Books were not changed. "
        "Please try again."
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

if "saved_books" not in st.session_state:
    st.session_state.saved_books = []

if "details_return_view" not in st.session_state:
    st.session_state.details_return_view = (
        "search"
    )

if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

if "auth_return_view" not in st.session_state:
    st.session_state.auth_return_view = (
        "search"
    )

if "flash_message" not in st.session_state:
    st.session_state.flash_message = None

if "registration_pending_email" not in st.session_state:
    st.session_state.registration_pending_email = None


current_user = get_current_user()
show_flash()


# =========================================================
# SIDEBAR NAVIGATION
# =========================================================


with st.sidebar:
    st.title("Open Library")
    st.caption("Navigation")

    if st.button(
        "Search Books",
        use_container_width=True
    ):
        st.session_state.view = "search"
        st.session_state.selected_book = None
        st.session_state.load_editions = False
        st.rerun()

    if current_user:
        saved_count = len(
            st.session_state.saved_books
        )

        if st.button(
            f"Saved Books ({saved_count})",
            use_container_width=True
        ):
            st.session_state.view = "saved"
            st.session_state.selected_book = None
            st.session_state.load_editions = False
            st.rerun()

        st.divider()

        with st.container(
            border=True
        ):
            st.caption(
                "YOUR ACCOUNT"
            )
            st.write(
                f"**{current_user['email']}**"
            )
            st.caption(
                f"{saved_count} saved book(s)"
            )

            if st.button(
                "Account",
                use_container_width=True
            ):
                st.session_state.view = "account"
                st.session_state.selected_book = None
                st.session_state.load_editions = False
                st.rerun()

            if st.button(
                "Logout",
                use_container_width=True
            ):
                try:
                    sign_out()
                except Exception:
                    # Clear local app state even if the remote
                    # sign-out request has a temporary problem.
                    st.session_state.auth_user = None

                st.session_state.saved_books = []
                st.session_state.view = "search"
                st.session_state.selected_book = None
                st.session_state.load_editions = False
                set_flash(
                    "You have been signed out.",
                    "👋"
                )
                st.rerun()

        st.caption(
            "Saved Books are stored in your "
            "account and persist across sessions."
        )

    else:
        if st.button(
            "Login",
            use_container_width=True
        ):
            return_view = (
                st.session_state.view
                if st.session_state.view
                in ["search", "details"]
                else "search"
            )
            open_login(
                return_view
            )

        if st.button(
            "Create Account",
            use_container_width=True
        ):
            st.session_state.registration_pending_email = None
            return_view = (
                st.session_state.view
                if st.session_state.view
                in ["search", "details"]
                else "search"
            )
            st.session_state.auth_return_view = (
                return_view
            )
            st.session_state.view = "register"
            st.rerun()

        st.divider()
        st.caption(
            "Search is public. "
            "Sign in to save books."
        )


# =========================================================
# LOGIN VIEW
# =========================================================


if st.session_state.view == "login":
    st.title("Login")
    st.caption(
        "Sign in to access Saved Books."
    )

    with st.form(
        "login_form"
    ):
        email = st.text_input(
            "Email",
            placeholder="you@example.com"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        login_submitted = (
            st.form_submit_button(
                "Login",
                type="primary"
            )
        )

    if login_submitted:
        clean_email = email.strip()

        if not clean_email or not password:
            st.warning(
                "Please enter your email "
                "and password."
            )
        else:
            try:
                with st.spinner(
                    "Signing in..."
                ):
                    response = sign_in(
                        clean_email,
                        password
                    )

                if response.user:
                    with st.spinner(
                        "Loading your saved books..."
                    ):
                        sync_saved_books()

                    target_view = (
                        st.session_state.auth_return_view
                    )

                    if target_view not in [
                        "search",
                        "details",
                        "saved",
                    ]:
                        target_view = "search"

                    st.session_state.view = (
                        target_view
                    )
                    set_flash(
                        "Welcome back!",
                        "👋"
                    )
                    st.rerun()
                else:
                    st.error(
                        "Login could not be completed."
                    )

            except Exception as error:
                st.error(
                    friendly_auth_error(
                        error,
                        "login"
                    )
                )

    st.write("")

    if st.button(
        "Create an account"
    ):
        st.session_state.registration_pending_email = None
        st.session_state.view = "register"
        st.rerun()

    if st.button(
        "← Back to Search"
    ):
        st.session_state.view = "search"
        st.rerun()

    st.stop()


# =========================================================
# REGISTER VIEW
# =========================================================


if st.session_state.view == "register":
    st.title("Create Account")

    pending_email = (
        st.session_state.registration_pending_email
    )

    if pending_email:
        st.success(
            "Your account was created."
        )
        st.info(
            "Check your email and confirm your account "
            "before logging in."
        )
        st.write(
            f"Confirmation sent to **{pending_email}**"
        )

        if st.button(
            "Go to Login",
            type="primary"
        ):
            st.session_state.registration_pending_email = None
            st.session_state.view = "login"
            st.rerun()

        if st.button(
            "← Back to Search"
        ):
            st.session_state.registration_pending_email = None
            st.session_state.view = "search"
            st.rerun()

        st.stop()

    st.caption(
        "Create an account with email "
        "and password."
    )
    st.caption(
        "Use a strong password you do not reuse elsewhere."
    )

    with st.form(
        "register_form"
    ):
        email = st.text_input(
            "Email",
            placeholder="you@example.com"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm password",
            type="password"
        )

        register_submitted = (
            st.form_submit_button(
                "Create Account",
                type="primary"
            )
        )

    if register_submitted:
        clean_email = email.strip()

        if not clean_email:
            st.warning(
                "Please enter an email address."
            )
        elif not password:
            st.warning(
                "Please enter a password."
            )
        elif password != confirm_password:
            st.warning(
                "Passwords do not match."
            )
        else:
            try:
                with st.spinner(
                    "Creating account..."
                ):
                    response = sign_up(
                        clean_email,
                        password
                    )

                if response.session:
                    st.success(
                        "Account created and "
                        "signed in."
                    )

                    with st.spinner(
                        "Loading your saved books..."
                    ):
                        sync_saved_books()

                    target_view = (
                        st.session_state.auth_return_view
                    )

                    if target_view not in [
                        "search",
                        "details",
                        "saved",
                    ]:
                        target_view = "search"

                    st.session_state.view = (
                        target_view
                    )
                    set_flash(
                        "Account created successfully.",
                        "🎉"
                    )
                    st.rerun()

                elif response.user:
                    st.session_state.registration_pending_email = (
                        clean_email
                    )
                    st.rerun()
                else:
                    st.error(
                        "Account could not be created."
                    )

            except Exception as error:
                st.error(
                    friendly_auth_error(
                        error,
                        "register"
                    )
                )

    st.write("")

    if st.button(
        "I already have an account"
    ):
        st.session_state.view = "login"
        st.rerun()

    if st.button(
        "← Back to Search"
    ):
        st.session_state.view = "search"
        st.rerun()

    st.stop()


# =========================================================
# BOOK DETAILS VIEW
# =========================================================


if (
    st.session_state.view == "details"
    and st.session_state.selected_book
):
    book = st.session_state.selected_book

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

    if (
        st.session_state.details_return_view
        == "saved"
        and current_user
    ):
        back_label = "← Back to Saved Books"
    else:
        back_label = "← Back to Results"

    if st.button(
        back_label
    ):
        return_view = (
            st.session_state.details_return_view
        )

        if (
            return_view == "saved"
            and not current_user
        ):
            return_view = "search"

        st.session_state.view = return_view
        st.session_state.selected_book = None
        st.session_state.load_editions = False

        if return_view == "search":
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

                if current_user:
                    if is_book_saved(
                        book,
                        st.session_state.saved_books
                    ):
                        if st.button(
                            "♥ Remove from Saved",
                            key="details_remove_saved",
                            use_container_width=True
                        ):
                            try:
                                remove_book_from_database(
                                    current_user["id"],
                                    book,
                                )
                                sync_saved_books()
                                set_flash(
                                    "Book removed from Saved Books.",
                                    "🗑️"
                                )
                                st.rerun()
                            except Exception:
                                show_saved_book_error(
                                    "remove"
                                )
                    else:
                        if st.button(
                            "♡ Save Book",
                            key="details_save_book",
                            type="primary",
                            use_container_width=True
                        ):
                            try:
                                save_book_to_database(
                                    current_user["id"],
                                    book,
                                )
                                sync_saved_books()
                                set_flash(
                                    "Book saved to your account.",
                                    "📚"
                                )
                                st.rerun()
                            except Exception:
                                show_saved_book_error(
                                    "save"
                                )
                else:
                    if st.button(
                        "Login to Save",
                        key="details_login_to_save",
                        use_container_width=True
                    ):
                        open_login(
                            "details"
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

                if availability_details[
                    "waitlist"
                ]:
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
                        (
                            edition_info_col1,
                            edition_info_col2,
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
# ACCOUNT VIEW
# =========================================================


if st.session_state.view == "account":
    if not current_user:
        open_login(
            "search"
        )

    st.title(
        "Account"
    )

    with st.container(
        border=True
    ):
        st.caption(
            "SIGNED IN AS"
        )
        st.subheader(
            current_user["email"]
        )

        account_saved_col, account_status_col = (
            st.columns(2)
        )

        with account_saved_col:
            st.metric(
                "Saved books",
                len(st.session_state.saved_books),
                border=True
            )

        with account_status_col:
            st.metric(
                "Account status",
                "Active",
                border=True
            )

        st.caption(
            "Your Saved Books are linked to this account "
            "and stored in Supabase."
        )

    st.write(
        ""
    )

    account_saved_button_col, account_search_button_col = (
        st.columns(2)
    )

    with account_saved_button_col:
        if st.button(
            "View Saved Books",
            type="primary",
            use_container_width=True
        ):
            st.session_state.view = "saved"
            st.rerun()

    with account_search_button_col:
        if st.button(
            "Back to Search",
            use_container_width=True
        ):
            st.session_state.view = "search"
            st.rerun()

    st.divider()

    if st.button(
        "Logout",
        use_container_width=True
    ):
        try:
            sign_out()
        except Exception:
            st.session_state.auth_user = None

        st.session_state.saved_books = []
        st.session_state.view = "search"
        st.session_state.selected_book = None
        st.session_state.load_editions = False
        set_flash(
            "You have been signed out.",
            "👋"
        )
        st.rerun()

    st.stop()


# =========================================================
# SAVED BOOKS VIEW
# =========================================================


if st.session_state.view == "saved":
    if not current_user:
        st.warning(
            "Please log in to access Saved Books."
        )

        if st.button(
            "Login",
            type="primary"
        ):
            open_login(
                "saved"
            )

        st.stop()

    st.title(
        "Saved Books"
    )

    st.caption(
        "Books saved to your account. "
        "They will still be here the next "
        "time you sign in."
    )

    if not st.session_state.saved_books:
        st.info(
            "You haven't saved any books yet. "
            "Search for a book and select "
            "'Save Book' to add it here."
        )

    else:
        st.write(
            f"**{len(st.session_state.saved_books)} "
            f"saved book(s)**"
        )

        for index, book in enumerate(
            st.session_state.saved_books
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

                with info_col:
                    st.markdown(
                        f"### {title}"
                    )

                    st.write(
                        f"**Author(s):** "
                        f"{authors_text}"
                    )

                    (
                        metadata_col1,
                        metadata_col2,
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

                    details_col, remove_col = (
                        st.columns(2)
                    )

                    with details_col:
                        if st.button(
                            "View Details",
                            key=(
                                f"saved_details_"
                                f"{index}"
                            ),
                            type="primary",
                            use_container_width=True
                        ):
                            st.session_state.selected_book = (
                                book
                            )

                            st.session_state.view = (
                                "details"
                            )

                            st.session_state.details_return_view = (
                                "saved"
                            )

                            st.session_state.load_editions = False
                            st.session_state.scroll_to_details = True
                            st.rerun()

                    with remove_col:
                        if st.button(
                            "Remove",
                            key=(
                                f"saved_remove_"
                                f"{index}"
                            ),
                            use_container_width=True
                        ):
                            try:
                                remove_book_from_database(
                                    current_user["id"],
                                    book,
                                )
                                sync_saved_books()
                                set_flash(
                                    "Book removed from Saved Books.",
                                    "🗑️"
                                )
                                st.rerun()
                            except Exception:
                                show_saved_book_error(
                                    "remove"
                                )

            st.write("")

    st.stop()


# =========================================================
# SEARCH VIEW
# =========================================================


if st.session_state.view == "search":
    st.title(
        "Open Library Book Search"
    )

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

    if search_submitted:
        clean_query = query.strip()

        if not clean_query:
            st.warning(
                "Please enter something "
                "to search."
            )
        else:
            search_is_valid = True

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

                        with info_col:
                            st.markdown(
                                f"### {title}"
                            )

                            st.write(
                                f"**Author(s):** "
                                f"{authors_text}"
                            )

                            (
                                metadata_col1,
                                metadata_col2,
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

                            details_col, save_col = (
                                st.columns(2)
                            )

                            with details_col:
                                if st.button(
                                    "View Details",
                                    key=(
                                        f"details_"
                                        f"{st.session_state.page}_"
                                        f"{index}"
                                    ),
                                    type="primary",
                                    use_container_width=True
                                ):
                                    st.session_state.selected_book = (
                                        book
                                    )

                                    st.session_state.view = (
                                        "details"
                                    )

                                    st.session_state.details_return_view = (
                                        "search"
                                    )

                                    st.session_state.load_editions = False
                                    st.session_state.scroll_to_details = True
                                    st.rerun()

                            with save_col:
                                if not current_user:
                                    if st.button(
                                        "Login to Save",
                                        key=(
                                            f"login_save_"
                                            f"{st.session_state.page}_"
                                            f"{index}"
                                        ),
                                        use_container_width=True
                                    ):
                                        open_login(
                                            "search"
                                        )

                                elif is_book_saved(
                                    book,
                                    st.session_state.saved_books
                                ):
                                    if st.button(
                                        "♥ Saved — Remove",
                                        key=(
                                            f"remove_result_"
                                            f"{st.session_state.page}_"
                                            f"{index}"
                                        ),
                                        use_container_width=True
                                    ):
                                        try:
                                            remove_book_from_database(
                                                current_user["id"],
                                                book,
                                            )
                                            sync_saved_books()
                                            set_flash(
                                                "Book removed from Saved Books.",
                                                "🗑️"
                                            )
                                            st.rerun()
                                        except Exception:
                                            show_saved_book_error(
                                                "remove"
                                            )

                                else:
                                    if st.button(
                                        "♡ Save Book",
                                        key=(
                                            f"save_result_"
                                            f"{st.session_state.page}_"
                                            f"{index}"
                                        ),
                                        use_container_width=True
                                    ):
                                        try:
                                            save_book_to_database(
                                                current_user["id"],
                                                book,
                                            )
                                            sync_saved_books()
                                            set_flash(
                                                "Book saved to your account.",
                                                "📚"
                                            )
                                            st.rerun()
                                        except Exception:
                                            show_saved_book_error(
                                                "save"
                                            )

                    st.write("")

                previous_col, next_col = (
                    st.columns(2)
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
