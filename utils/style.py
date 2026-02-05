import streamlit as st

def apply_global_style():
    st.markdown(
        """
        <style>
        /* Remove Streamlit default padding */
        .block-container {
            padding-top: 2rem;
            padding-left: 3rem;
            padding-right: 3rem;
        }

        /* Headings */
        h1, h2, h3 {
            font-weight: 600;
        }

        /* Cards */
        .card {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }

        /* Upload area */
        section[data-testid="stFileUploader"] {
            border-radius: 12px;
            padding: 20px;
            background-color: #f9fafb;
        }

        /* Buttons */
        button[kind="primary"] {
            border-radius: 8px;
            height: 42px;
            font-weight: 500;
        }

        </style>
        """,
        unsafe_allow_html=True
    )
