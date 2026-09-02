"""Global Streamlit styles."""

from __future__ import annotations

import streamlit as st


def load_global_styles() -> None:
    """Load the existing lightweight application shell styles."""
    st.markdown(
        """
        <style>
        :root { --ink:#182230; --muted:#667085; --line:#E4E7EC; --accent:#3448C5; }
        .stApp { background:radial-gradient(circle at 8% 0%,rgba(52,72,197,.08),transparent 30rem),#F8FAFC; }
        .block-container { max-width:1180px; padding-top:2.2rem; padding-bottom:3rem; }
        h1,h2,h3 { color:var(--ink); letter-spacing:-.02em; }
        [data-testid="stMetric"] { background:#FFF; border:1px solid var(--line); padding:1rem; border-radius:12px; }
        [data-testid="stSidebar"] { border-right:1px solid var(--line); }
        .product-label { color:var(--accent); font-weight:800; letter-spacing:.08em; text-transform:uppercase; font-size:.72rem; }
        .product-copy { color:var(--muted); line-height:1.55; font-size:.9rem; }
        .stButton > button[kind="primary"] { background:var(--accent); border-color:var(--accent); }
        #MainMenu, footer { visibility:hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )
