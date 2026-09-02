"""Global Streamlit styles."""

from __future__ import annotations

import streamlit as st


def load_global_styles() -> None:
    """Load the compact Sentiment AI visual system."""
    st.markdown(
        """
        <style>
        :root {
            --navy:#172554; --accent:#4F46E5; --accent-soft:#EEF2FF;
            --canvas:#F8FAFC; --surface:#FFFFFF; --ink:#172033;
            --muted:#64748B; --line:#E2E8F0; --positive:#15803D;
            --negative:#B42318; --neutral:#526174; --warning:#B54708;
            --radius:14px; --shadow:0 1px 2px rgba(15,23,42,.04),0 8px 24px rgba(15,23,42,.035);
        }
        .stApp { background:var(--canvas); color:var(--ink); }
        .block-container { max-width:1180px; padding-top:1.5rem; padding-bottom:3rem; }
        h1,h2,h3 { color:var(--navy); letter-spacing:-.025em; }
        p, [data-testid="stCaptionContainer"] { color:var(--muted); }
        [data-testid="stMetric"] {
            background:var(--surface); border:1px solid var(--line);
            padding:1rem 1.1rem; border-radius:var(--radius); box-shadow:var(--shadow);
        }
        [data-testid="stMetricLabel"] { color:var(--muted); }
        [data-testid="stMetricValue"] { color:var(--navy); letter-spacing:-.025em; }
        [data-testid="stSidebar"] { background:#F1F5F9; border-right:1px solid var(--line); }
        [data-testid="stForm"], [data-testid="stFileUploader"] {
            background:var(--surface); border:1px solid var(--line);
            border-radius:var(--radius); padding:1.15rem; box-shadow:var(--shadow);
        }
        .product-label { color:var(--accent); font-weight:800; letter-spacing:.09em; text-transform:uppercase; font-size:.7rem; }
        .product-copy { color:var(--muted); line-height:1.55; font-size:.88rem; }
        .stButton > button, .stDownloadButton > button { border-radius:10px; font-weight:650; min-height:2.65rem; }
        .stButton > button[kind="primary"] { background:var(--accent); border-color:var(--accent); box-shadow:0 4px 12px rgba(79,70,229,.18); }
        .stButton > button[kind="primary"]:hover { background:var(--navy); border-color:var(--navy); }
        [data-testid="stAlert"] { border-radius:12px; }
        hr { border-color:var(--line); }
        #MainMenu, footer { visibility:hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )
