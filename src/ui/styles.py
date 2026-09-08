"""Global Streamlit styles."""

from __future__ import annotations

import streamlit as st


def load_global_styles() -> None:
    """Load the compact Sentiment AI visual system."""
    st.markdown(
        """
        <style>
        :root {
            --navy:#10243E; --navy-raised:#163452; --accent:#16856B;
            --accent-soft:#E7F5F0; --canvas:#F4F6F4; --surface:#FFFFFF;
            --ink:#10243E; --muted:#687781; --line:#DFE5E5;
            --positive:#16856B; --negative:#D55C47; --neutral:#687781;
            --warning:#C78A2C; --radius:14px;
            --shadow:0 1px 2px rgba(16,36,62,.04),0 12px 30px rgba(16,36,62,.055);
        }
        .stApp { background:var(--canvas); color:var(--ink); }
        .block-container { max-width:1440px; padding:1.85rem clamp(1.25rem,3.2vw,3.25rem) 4rem; }
        h1,h2,h3 { color:var(--navy); letter-spacing:-.025em; }
        p, [data-testid="stCaptionContainer"] { color:var(--muted); }
        [data-testid="stMetric"] {
            background:var(--surface); border:1px solid var(--line);
            padding:1rem 1.1rem; border-radius:var(--radius); box-shadow:var(--shadow);
        }
        [data-testid="stMetricLabel"] { color:var(--muted); }
        [data-testid="stMetricValue"] { color:var(--navy); letter-spacing:-.025em; }
        [data-testid="stSidebar"] { background:var(--navy); border-right:0; }
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

        /* Legacy product header (kept for non-active compatibility) */
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

        /* Customer intelligence application shell */
        .workspace-brand {
            display:flex; align-items:center; gap:.7rem; padding:.35rem .35rem 1.25rem;
        }
        .workspace-mark {
            width:2rem; height:2rem; display:flex; align-items:flex-end; justify-content:center;
            gap:3px; padding:.43rem; border-radius:9px; background:#F0F5F2;
        }
        .workspace-mark i { width:4px; border-radius:4px; background:var(--positive); }
        .workspace-mark i:nth-child(1) { height:7px; }
        .workspace-mark i:nth-child(2) { height:15px; }
        .workspace-mark i:nth-child(3) { height:11px; }
        .workspace-brand strong { display:block; color:#FFF; font-size:.94rem; line-height:1.2; }
        .workspace-brand span { display:block; color:#8DA2B4; font-size:.66rem; margin-top:.15rem; }
        .workspace-nav-groups {
            display:flex; align-items:center; gap:.35rem; padding:0 .45rem .7rem;
            color:#6F899F; font-size:.57rem; font-weight:750; letter-spacing:.09em;
            text-transform:uppercase;
        }
        .workspace-nav-groups i { width:3px; height:3px; border-radius:50%; background:#49647B; }
        [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] { gap:.2rem; }
        [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label {
            min-height:2.35rem; padding:.48rem .65rem; color:#AEBECB; border-radius:8px;
            font-size:.79rem; border:1px solid transparent;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:hover {
            color:#FFF; background:rgba(255,255,255,.055);
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
            color:#FFF; background:#1E466B; border-color:rgba(255,255,255,.035);
            box-shadow:inset 2px 0 0 #4FB69C;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label span {
            color:inherit;
        }
        .workspace-dataset {
            margin:1.3rem .1rem .75rem; padding:.8rem; border-radius:11px;
            border:1px solid rgba(255,255,255,.1); background:rgba(255,255,255,.045);
        }
        .workspace-dataset-label {
            display:flex; align-items:center; gap:.4rem; margin-bottom:.55rem; color:#8DA2B4;
            font-size:.58rem; font-weight:750; letter-spacing:.1em; text-transform:uppercase;
        }
        .workspace-dataset-label i { width:6px; height:6px; border-radius:50%; background:#71899D; }
        .workspace-dataset.is-active .workspace-dataset-label i {
            background:#56C7A8; box-shadow:0 0 0 4px rgba(86,199,168,.1);
        }
        .workspace-dataset strong { display:block; color:#FFF; font-size:.77rem; }
        .workspace-dataset > span { display:block; color:#A1B2BF; font-size:.65rem; margin-top:.2rem; }
        .workspace-dataset small {
            display:block; color:#71899D; font-size:.56rem; line-height:1.4;
            border-top:1px solid rgba(255,255,255,.08); margin-top:.65rem; padding-top:.55rem;
        }
        .workspace-signature {
            display:flex; align-items:center; gap:.55rem; border-top:1px solid rgba(255,255,255,.08);
            margin:.35rem .1rem 0; padding:.85rem .25rem .15rem;
        }
        .workspace-signature > span {
            width:1.8rem; height:1.8rem; display:grid; place-items:center; border-radius:50%;
            background:#294C69; color:#FFF; font-size:.6rem; font-weight:750;
        }
        .workspace-signature div { flex:1; }
        .workspace-signature strong,.workspace-signature small { display:block; }
        .workspace-signature strong { color:#DCE5EB; font-size:.64rem; }
        .workspace-signature small { color:#71899D; font-size:.56rem; margin-top:.1rem; }
        .workspace-signature b { color:#71899D; font-size:.56rem; }
        .workspace-page-eyebrow {
            color:var(--positive); font-size:.64rem; font-weight:800; letter-spacing:.13em;
            text-transform:uppercase; margin:.25rem 0 -.3rem;
        }
        h2[id^="workspace-page-"] {
            color:var(--navy); font-size:clamp(1.8rem,3vw,2.5rem); line-height:1.1;
            letter-spacing:-.045em; margin-bottom:.15rem;
        }
        .workspace-page-description {
            color:var(--muted); font-size:.88rem; margin:-.35rem 0 1.7rem;
        }
        .workspace-empty-state {
            min-height:17rem; display:flex; align-items:center; justify-content:center; gap:1rem;
            padding:2rem; border:1px dashed #BDC9C7; border-radius:var(--radius);
            background:rgba(255,255,255,.62); text-align:left;
        }
        .workspace-empty-icon {
            width:3rem; height:3rem; display:grid; place-items:center; flex:0 0 auto;
            border-radius:13px; background:var(--accent-soft); color:var(--positive); font-size:1.2rem;
        }
        .workspace-empty-state strong { color:var(--navy); font-size:1rem; }
        .workspace-empty-state p { max-width:30rem; margin:.3rem 0 0; font-size:.8rem; line-height:1.5; }
        @media (max-width: 768px) {
            .block-container { padding:1.2rem 1rem 3rem; }
            .workspace-page-eyebrow { margin-top:.1rem; }
            h2[id^="workspace-page-"] { font-size:1.75rem; }
            .workspace-empty-state { min-height:13rem; flex-direction:column; text-align:center; }
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
