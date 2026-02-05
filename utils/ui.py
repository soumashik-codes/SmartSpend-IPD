import streamlit as st
from utils.auth import logout_user

def top_right_auth():
    """
    Displays username and logout button in top-right area.
    Call this in app.py and protected pages.
    """
    col_spacer, col_user = st.columns([6, 2])

    with col_user:
        if st.session_state.get("logged_in"):
            st.markdown(
                f"""
                <div style="text-align:right;">
                    <p style="margin:0; font-size:0.9rem; color:#16a34a;">
                        👤 {st.session_state.get("username")}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("Log out", key="logout_top"):
                logout_user()
                st.switch_page("app.py")
