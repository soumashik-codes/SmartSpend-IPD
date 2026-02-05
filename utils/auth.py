import streamlit as st
import bcrypt
from utils.database import init_db, get_conn


# Session handling
def init_session():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "first_name" not in st.session_state:
        st.session_state.first_name = None
    if "last_name" not in st.session_state:
        st.session_state.last_name = None


# User creation
def create_user(
    username: str,
    first_name: str,
    last_name: str,
    password: str
) -> tuple[bool, str]:
    """
    Creates a new user account.
    """
    init_db()
    conn = get_conn()
    cur = conn.cursor()

    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    )

    try:
        cur.execute(
            """
            INSERT INTO users (username, first_name, last_name, password_hash)
            VALUES (?, ?, ?, ?)
            """,
            (username, first_name, last_name, password_hash)
        )
        conn.commit()
        return True, "Account created successfully. Please log in."
    except Exception:
        return False, "Username already exists."
    finally:
        conn.close()


# Authentication
def verify_user(username: str, password: str) -> tuple[bool, str, int | None, str | None, str | None]:
    """
    Verifies user credentials.

    Returns:
        (success, message, user_id, first_name, last_name)
    """
    init_db()
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, first_name, last_name, password_hash
        FROM users
        WHERE username = ?
        """,
        (username,)
    )

    row = cur.fetchone()
    conn.close()

    if not row:
        return False, "User not found.", None, None, None

    user_id, first_name, last_name, stored_hash = row

    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode("utf-8")

    if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
        return True, "Login successful.", user_id, first_name, last_name

    return False, "Incorrect password.", None, None, None


# Login / logout

def login_user(username: str, user_id: int, first_name: str, last_name: str):
    st.session_state.logged_in = True
    st.session_state.username = username
    st.session_state.user_id = user_id
    st.session_state.first_name = first_name
    st.session_state.last_name = last_name


def logout_user():
    for key in [
        "logged_in",
        "username",
        "user_id",
        "first_name",
        "last_name"
    ]:
        if key in st.session_state:
            del st.session_state[key]


def require_login():
    if not st.session_state.get("logged_in", False):
        st.warning("Please log in to continue.")
        st.stop()
