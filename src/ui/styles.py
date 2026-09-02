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

        /* Compact Product Header */
        .product-header {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: var(--radius);
            padding: 1rem 1.35rem;
            margin-bottom: 1.5rem;
            box-shadow: var(--shadow);
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1.25rem;
            box-sizing: border-box;
            max-height: 140px;
        }
        .product-header-main {
            display: flex;
            flex-direction: column;
            gap: 0.15rem;
        }
        .product-header-eyebrow {
            color: var(--accent);
            font-weight: 800;
            letter-spacing: .09em;
            text-transform: uppercase;
            font-size: .7rem;
        }
        .product-header-title {
            font-size: 1.65rem;
            font-weight: 800;
            line-height: 1.2;
            margin: 0;
            color: var(--navy);
            letter-spacing: -.025em;
        }
        .product-header-description {
            font-size: .88rem;
            color: var(--muted);
            margin: 0.15rem 0 0;
            line-height: 1.4;
        }
        .product-header-tagline {
            font-size: .78rem;
            font-weight: 600;
            color: var(--muted);
            background: var(--canvas);
            border: 1px solid var(--line);
            border-radius: 9999px;
            padding: .35rem .85rem;
            white-space: nowrap;
        }
        @media (max-width: 768px) {
            .product-header {
                flex-direction: column;
                align-items: flex-start;
                gap: .75rem;
                max-height: none;
            }
        }

        /* Sidebar Brand */
        .sidebar-brand {
            padding-bottom: .5rem;
            margin-bottom: .5rem;
            border-bottom: 1px solid var(--line);
        }
        .sidebar-brand-title {
            font-size: 1.15rem;
            font-weight: 750;
            color: var(--navy);
            letter-spacing: -.02em;
        }

        /* Estilos generales del radio (sin selectores posicionales) */
        [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label {
            padding: 0.35rem 0.6rem;
            border-radius: 8px;
            transition: background .15s ease;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:hover {
            background: rgba(79, 70, 229, .05);
        }

        /* Sidebar Discrete Batch Status & Footer */
        .sidebar-batch-status {
            display: flex;
            align-items: center;
            gap: .5rem;
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: .5rem .75rem;
            font-size: .8rem;
            color: var(--ink);
            margin-top: 1.5rem;
            margin-bottom: .5rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, .03);
        }
        .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--positive);
            display: inline-block;
            flex-shrink: 0;
        }
        .sidebar-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: .75rem .2rem .2rem;
            border-top: 1px solid var(--line);
            margin-top: 1rem;
        }
        .sidebar-footer-title {
            font-size: .75rem;
            font-weight: 600;
            color: var(--muted);
        }
        .sidebar-footer-badge {
            font-size: .68rem;
            font-weight: 700;
            letter-spacing: .04em;
            color: var(--accent);
            background: var(--accent-soft);
            padding: .15rem .5rem;
            border-radius: 6px;
        }

        /* Sentiment Badges & Result Presentation */
        .sentiment-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.28rem 0.8rem;
            border-radius: 9999px;
            font-size: 0.78rem;
            font-weight: 750;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        .badge-positive {
            background: #ECFDF3;
            color: var(--positive);
            border: 1px solid #A6F4C5;
        }
        .badge-negative {
            background: #FEF3F2;
            color: var(--negative);
            border: 1px solid #FECDCA;
        }
        .badge-neutral {
            background: #F8FAFC;
            color: var(--neutral);
            border: 1px solid #E2E8F0;
        }
        .origin-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.22rem 0.65rem;
            border-radius: 6px;
            font-size: 0.72rem;
            font-weight: 650;
            background: var(--accent-soft);
            color: var(--accent);
            border: 1px solid rgba(79, 70, 229, 0.15);
        }
        /* Batch Upload Card */
        .batch-upload-card {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: var(--radius);
            padding: 1.5rem 1.35rem;
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
        }
        .batch-upload-title {
            font-size: 1.35rem;
            font-weight: 750;
            color: var(--navy);
            letter-spacing: -.02em;
            margin: 0 0 .25rem;
        }
        .batch-upload-description {
            font-size: .88rem;
            color: var(--muted);
            line-height: 1.5;
            margin: 0 0 .15rem;
        }

        /* Batch Privacy Callout */
        .batch-privacy-callout {
            display: flex;
            align-items: flex-start;
            gap: .6rem;
            background: var(--accent-soft);
            border: 1px solid rgba(79, 70, 229, .12);
            border-radius: 10px;
            padding: .65rem .9rem;
            margin-top: .75rem;
            font-size: .8rem;
            color: var(--accent);
            line-height: 1.45;
        }
        .batch-privacy-callout .privacy-icon {
            flex-shrink: 0;
            font-size: 1rem;
            margin-top: .05rem;
        }

        /* Batch CSV Preview Summary */
        .batch-csv-summary {
            display: flex;
            gap: .75rem;
            flex-wrap: wrap;
            margin-bottom: .75rem;
        }
        .batch-csv-chip {
            display: inline-flex;
            align-items: center;
            gap: .35rem;
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: .4rem .75rem;
            font-size: .82rem;
            color: var(--ink);
            box-shadow: 0 1px 2px rgba(15, 23, 42, .03);
        }
        .batch-csv-chip strong {
            color: var(--navy);
            font-weight: 700;
        }

        /* Batch Summary Band (post-processing) */
        .batch-summary-band {
            display: flex;
            align-items: center;
            gap: .75rem;
            flex-wrap: wrap;
            background: #ECFDF3;
            border: 1px solid #A6F4C5;
            border-radius: 10px;
            padding: .7rem 1rem;
            margin: .75rem 0;
            font-size: .85rem;
            color: var(--positive);
        }
        .batch-summary-band .band-item {
            display: inline-flex;
            align-items: center;
            gap: .3rem;
        }
        .batch-summary-band .band-separator {
            color: #A6F4C5;
            font-weight: 300;
        }
        .batch-summary-band strong {
            font-weight: 750;
        }

        /* Batch Section Header */
        .batch-section-header {
            margin: 1.5rem 0 .75rem;
        }
        .batch-section-header h3 {
            font-size: 1.15rem;
            font-weight: 750;
            color: var(--navy);
            margin: 0 0 .15rem;
            letter-spacing: -.02em;
        }
        .batch-section-header p {
            font-size: .85rem;
            color: var(--muted);
            margin: 0;
            line-height: 1.45;
        }

        /* Batch KPI Row */
        .batch-kpi-row {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: .65rem;
            margin-bottom: 1rem;
        }
        .batch-kpi-card {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: var(--radius);
            padding: .85rem 1rem;
            box-shadow: var(--shadow);
            text-align: center;
        }
        .batch-kpi-label {
            font-size: .72rem;
            font-weight: 650;
            text-transform: uppercase;
            letter-spacing: .06em;
            color: var(--muted);
            margin-bottom: .25rem;
        }
        .batch-kpi-value {
            font-size: 1.5rem;
            font-weight: 800;
            color: var(--navy);
            letter-spacing: -.025em;
            line-height: 1.2;
        }
        .batch-kpi-sub {
            font-size: .75rem;
            color: var(--muted);
            margin-top: .15rem;
        }
        @media (max-width: 768px) {
            .batch-kpi-row {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        @media (max-width: 480px) {
            .batch-kpi-row {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
