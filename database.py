import streamlit as st

from supabase import Client, create_client


def get_supabase_client():
    """
    Return one Supabase client for the current Streamlit session.

    We intentionally keep this client in st.session_state instead of
    using st.cache_resource because authentication belongs to one user
    session and must not be shared between visitors.
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

    # If email confirmation is disabled, Supabase may return
    # a session immediately. In that case, log the user in.
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
