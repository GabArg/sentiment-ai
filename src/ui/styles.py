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
        .block-container {
            width:100%; max-width:1520px;
            padding:1.85rem clamp(1.25rem,2.5vw,2.5rem) 4rem;
        }
        h1,h2,h3 { color:var(--navy); letter-spacing:-.025em; }
        p, [data-testid="stCaptionContainer"] { color:var(--muted); }
        [data-testid="stMetric"] {
            background:var(--surface); border:1px solid var(--line);
            padding:1rem 1.1rem; border-radius:var(--radius); box-shadow:var(--shadow);
        }
        [data-testid="stMetricLabel"] { color:var(--muted); }
        [data-testid="stMetricValue"] { color:var(--navy); letter-spacing:-.025em; }
        [data-testid="stSidebar"] {
            min-width:16rem; max-width:16rem; background:var(--navy); border-right:0;
        }
        [data-testid="stForm"], [data-testid="stFileUploader"] {
            background:var(--surface); border:1px solid var(--line);
            border-radius:var(--radius); padding:1.15rem; box-shadow:var(--shadow);
        }
        .product-label { color:var(--accent); font-weight:800; letter-spacing:.09em; text-transform:uppercase; font-size:.7rem; }
        .product-copy { color:var(--muted); line-height:1.55; font-size:.88rem; }
        .stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
            border-radius:10px; font-weight:650; min-height:2.65rem;
        }
        :is(.stButton, .stFormSubmitButton) > button[kind="primary"] {
            background:var(--accent); border-color:var(--accent); color:#FFF;
            box-shadow:0 4px 12px rgba(22,133,107,.2);
        }
        :is(.stButton, .stFormSubmitButton) > button[kind="primary"] :is(p, span) {
            color:inherit !important;
        }
        :is(.stButton, .stFormSubmitButton) > button[kind="primary"]:hover:not(:disabled) {
            background:var(--navy); border-color:var(--navy); color:#FFF;
        }
        :is(.stButton, .stFormSubmitButton) > button[kind="primary"]:active:not(:disabled) {
            background:var(--navy-raised); border-color:var(--navy-raised); color:#FFF;
            box-shadow:inset 0 2px 4px rgba(0,0,0,.18);
        }
        :is(.stButton, .stFormSubmitButton) > button[kind="primary"]:focus-visible {
            color:#FFF; outline:3px solid rgba(22,133,107,.32); outline-offset:2px;
        }
        :is(.stButton, .stFormSubmitButton) > button[kind="primary"]:disabled {
            background:#526B65; border-color:#526B65; color:#FFF;
            box-shadow:none; opacity:1; cursor:not-allowed;
        }
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
        [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {
            gap:.18rem; padding-top:.55rem;
        }
        [data-testid="stSidebar"] label[data-baseweb="radio"] {
            min-height:2.35rem; padding:.48rem .65rem; color:#AEBECB; border-radius:8px;
            font-size:.79rem; border:1px solid transparent; position:relative;
        }
        [data-testid="stSidebar"] label[data-baseweb="radio"] [aria-hidden="true"] { display:none; }
        [data-testid="stSidebar"] label[data-baseweb="radio"] input[type="radio"] {
            position:absolute; width:1px; height:1px; opacity:0; pointer-events:none;
        }
        [data-testid="stSidebar"] label[data-baseweb="radio"]:hover {
            color:#FFF; background:rgba(255,255,255,.055);
        }
        [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) {
            color:#FFF; background:#1E466B; border-color:rgba(255,255,255,.035);
            box-shadow:inset 2px 0 0 #4FB69C;
        }
        [data-testid="stSidebar"] label[data-baseweb="radio"] span { color:inherit; }
        [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input[value="Dashboard"]),
        [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input[value="Informe ejecutivo"]),
        [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input[value="Acerca del proyecto"]) {
            margin-top:1.25rem;
        }
        [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input[value="Análisis individual"])::before,
        [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input[value="Dashboard"])::before,
        [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input[value="Informe ejecutivo"])::before,
        [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input[value="Acerca del proyecto"])::before {
            position:absolute; left:.15rem; top:-1rem; color:#6F899F; font-size:.56rem;
            font-weight:800; letter-spacing:.13em; text-transform:uppercase;
        }
        [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input[value="Análisis individual"])::before { content:"Analizar"; }
        [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input[value="Dashboard"])::before { content:"Entender"; }
        [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input[value="Informe ejecutivo"])::before { content:"Comunicar"; }
        [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input[value="Acerca del proyecto"])::before { content:"Proyecto"; }
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

        /* Customer feedback overview */
        .overview-kpi-grid {
            display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:.85rem;
            margin:0 0 .9rem;
        }
        .overview-kpi {
            position:relative; overflow:hidden; min-height:7.4rem; padding:1rem 1.1rem;
            border:1px solid var(--line); border-radius:var(--radius); background:var(--surface);
            box-shadow:var(--shadow);
        }
        .overview-kpi.negative::before {
            content:""; position:absolute; inset:0 auto 0 0; width:3px; background:var(--negative);
        }
        .overview-kpi > div { display:flex; align-items:center; justify-content:space-between; }
        .overview-kpi > div span {
            color:var(--muted); font-size:.66rem; font-weight:650; letter-spacing:.01em;
        }
        .overview-kpi > div i { width:7px; height:7px; border-radius:50%; background:#AEB9BA; }
        .overview-kpi.positive > div i { background:var(--positive); }
        .overview-kpi.negative > div i { background:var(--negative); }
        .overview-kpi.technical > div i { background:#4A7FA7; }
        .overview-kpi > strong {
            display:block; margin:.72rem 0 .32rem; color:var(--navy); font-size:1.65rem;
            line-height:1; letter-spacing:-.04em;
        }
        .overview-kpi > small { color:#879399; font-size:.61rem; }
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color:var(--line); border-radius:var(--radius); background:var(--surface);
            box-shadow:var(--shadow);
        }
        .overview-panel-heading { padding:.15rem .2rem 0; }
        .overview-panel-heading > span,.overview-attention-title > span {
            display:block; color:var(--positive); font-size:.58rem; font-weight:800;
            letter-spacing:.13em; text-transform:uppercase; margin-bottom:.22rem;
        }
        .overview-panel-heading h3,.overview-attention-title h3 {
            color:var(--navy); font-size:1rem; margin:0; letter-spacing:-.025em;
        }
        .overview-panel-heading p { color:var(--muted); font-size:.67rem; margin:.3rem 0 0; }
        .overview-attention,.overview-reading {
            height:100%; min-height:24rem; padding:1.15rem 1.2rem;
            border:1px solid var(--line); border-radius:var(--radius); background:var(--surface);
            box-shadow:var(--shadow);
        }
        .overview-attention-title > span { color:var(--negative); }
        .overview-critical-summary {
            display:flex; align-items:center; gap:.75rem; padding:.8rem; margin:1rem 0 .35rem;
            border-radius:10px; background:#FFF0EC;
        }
        .overview-critical-summary > i {
            display:grid; place-items:center; flex:0 0 auto; width:2rem; height:2rem;
            border-radius:9px; background:#FFF; color:var(--negative); font-style:normal; font-weight:800;
        }
        .overview-critical-summary strong { color:var(--navy); font-size:.78rem; }
        .overview-critical-summary p { color:#916F68; font-size:.59rem; line-height:1.4; margin:.14rem 0 0; }
        .overview-topic-row {
            display:grid; grid-template-columns:1.7rem minmax(0,1fr) auto; align-items:center;
            gap:.6rem; padding:.78rem .1rem; border-bottom:1px solid #EDF0EF;
        }
        .overview-topic-row > span { color:#A3ADB2; font-size:.58rem; font-weight:750; }
        .overview-topic-row strong,.overview-topic-row small { display:block; }
        .overview-topic-row strong { color:var(--ink); font-size:.71rem; }
        .overview-topic-row small { color:#8A969C; font-size:.54rem; margin-top:.16rem; }
        .overview-topic-row > b { color:var(--navy); font-size:.8rem; }
        .overview-no-topics { color:var(--muted); font-size:.68rem; padding:1.2rem .2rem; line-height:1.5; }
        .overview-attention-empty { padding:2.6rem .6rem; text-align:center; }
        .overview-attention-empty i {
            display:grid; place-items:center; width:2.6rem; height:2.6rem; margin:0 auto .7rem;
            border-radius:12px; background:var(--accent-soft); color:var(--positive); font-style:normal;
        }
        .overview-attention-empty strong { display:block; color:var(--navy); font-size:.78rem; }
        .overview-attention-empty p { color:var(--muted); font-size:.62rem; line-height:1.5; }
        .overview-method-note {
            color:#8A969C; font-size:.56rem; line-height:1.45; margin:1rem 0 0;
            padding-top:.7rem; border-top:1px solid #EDF0EF;
        }
        .overview-reading { min-height:20.5rem; }
        .overview-reading .overview-attention-title > span { color:var(--positive); }
        .overview-reading-grid { display:grid; grid-template-columns:1fr 1fr; gap:.6rem; margin:1rem 0; }
        .overview-reading-grid > div { padding:.8rem; border-radius:9px; background:#F4F7F6; }
        .overview-reading-grid strong,.overview-reading-grid span { display:block; }
        .overview-reading-grid strong { color:var(--navy); font-size:1.15rem; }
        .overview-reading-grid span { color:var(--muted); font-size:.57rem; line-height:1.4; margin-top:.2rem; }
        .overview-trace { padding:.8rem; border:1px solid var(--line); border-radius:9px; }
        .overview-trace strong { color:var(--navy); font-size:.65rem; }
        .overview-trace p { color:var(--muted); font-size:.58rem; line-height:1.55; margin:.25rem 0 0; }
        @media (max-width: 1050px) {
            .overview-kpi-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
        }
        @media (max-width: 600px) {
            .overview-kpi-grid { grid-template-columns:1fr; }
            .overview-kpi { min-height:6.7rem; }
            .overview-attention,.overview-reading { min-height:auto; }
            .overview-reading-grid { grid-template-columns:1fr; }
        }

        /* Pareto priority view */
        .pareto-summary-grid {
            display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.85rem; margin-bottom:.9rem;
        }
        .pareto-summary-card {
            position:relative; overflow:hidden; min-height:7.2rem; padding:1rem 1.1rem;
            border:1px solid var(--line); border-radius:var(--radius); background:var(--surface);
            box-shadow:var(--shadow);
        }
        .pareto-summary-card.negative::before {
            content:""; position:absolute; inset:0 auto 0 0; width:3px; background:var(--negative);
        }
        .pareto-summary-card > span,.pareto-summary-card > strong,.pareto-summary-card > small { display:block; }
        .pareto-summary-card > span { color:var(--muted); font-size:.66rem; font-weight:650; }
        .pareto-summary-card > strong {
            color:var(--navy); font-size:1.65rem; line-height:1; letter-spacing:-.04em; margin:.72rem 0 .34rem;
        }
        .pareto-summary-card > small { color:#879399; font-size:.59rem; line-height:1.4; }
        .pareto-ranking-panel {
            height:100%; min-height:25rem; padding:1.15rem 1.2rem; border:1px solid var(--line);
            border-radius:var(--radius); background:var(--surface); box-shadow:var(--shadow);
        }
        .pareto-section-heading > span {
            display:block; color:var(--negative); font-size:.58rem; font-weight:800;
            letter-spacing:.13em; text-transform:uppercase; margin-bottom:.22rem;
        }
        .pareto-section-heading h3 { color:var(--navy); font-size:1rem; margin:0; }
        .pareto-section-heading p { color:var(--muted); font-size:.62rem; margin:.3rem 0 0; }
        .pareto-ranking-list { margin-top:.85rem; }
        .pareto-ranking-row {
            display:grid; grid-template-columns:1.7rem minmax(0,1fr) auto; gap:.6rem;
            align-items:center; padding:.72rem .1rem; border-bottom:1px solid #EDF0EF;
        }
        .pareto-ranking-row > span { color:#A3ADB2; font-size:.58rem; font-weight:750; }
        .pareto-ranking-row strong,.pareto-ranking-row small { display:block; }
        .pareto-ranking-row strong { color:var(--ink); font-size:.72rem; }
        .pareto-ranking-row small { color:#8A969C; font-size:.54rem; margin-top:.16rem; }
        .pareto-ranking-row > b { color:var(--navy); font-size:.8rem; }
        .pareto-ranking-row > i {
            grid-column:2 / 4; color:var(--negative); font-size:.52rem; font-style:normal; margin-top:-.45rem;
        }
        .pareto-ranking-note {
            color:#8A969C; font-size:.56rem; line-height:1.45; margin:.9rem 0 0;
            padding-top:.65rem; border-top:1px solid #EDF0EF;
        }
        .pareto-methodology {
            display:flex; align-items:flex-start; gap:.75rem; margin:.9rem 0;
            padding:.9rem 1rem; border:1px solid #D7E7E1; border-radius:11px; background:#EDF5F2;
        }
        .pareto-methodology > div {
            display:grid; place-items:center; flex:0 0 auto; width:1.7rem; height:1.7rem;
            border-radius:50%; background:var(--surface); color:var(--positive); font-weight:800;
        }
        .pareto-methodology p { color:#526D64; font-size:.64rem; line-height:1.55; margin:0; }
        .pareto-methodology strong { color:#274B40; }
        @media (max-width: 850px) {
            .pareto-summary-grid { grid-template-columns:1fr; }
            .pareto-summary-card { min-height:6.5rem; }
            .pareto-ranking-panel { min-height:auto; }
        }

        /* Executive brief */
        .report-status {
            display:flex; align-items:center; justify-content:space-between; gap:1rem;
            padding:.85rem 1rem; margin-bottom:.9rem; border:1px solid #D4E6DF;
            border-radius:11px; background:#EDF5F2;
        }
        .report-status > div { display:flex; align-items:center; gap:.7rem; }
        .report-status i {
            display:grid; place-items:center; width:1.8rem; height:1.8rem; border-radius:50%;
            background:var(--positive); color:#FFF; font-style:normal; font-weight:800;
        }
        .report-status span strong,.report-status span small { display:block; }
        .report-status span strong { color:#274B40; font-size:.72rem; }
        .report-status span small { color:#658077; font-size:.57rem; margin-top:.14rem; }
        .report-status > b {
            padding:.3rem .55rem; border-radius:999px; background:var(--surface);
            color:var(--positive); font-size:.57rem; text-transform:uppercase; letter-spacing:.08em;
        }
        .report-section-heading { padding:.1rem .1rem .55rem; border-bottom:1px solid #EDF0EF; }
        .report-section-heading span {
            display:block; color:var(--positive); font-size:.56rem; font-weight:800;
            letter-spacing:.13em; text-transform:uppercase; margin-bottom:.2rem;
        }
        .report-section-heading.attention span { color:var(--negative); }
        .report-section-heading.limitations span { color:var(--warning); }
        .report-section-heading h3 { color:var(--navy); font-size:.98rem; margin:0; }
        .report-ai-intro {
            padding:1.1rem 1.2rem; margin:.1rem 0 .8rem; border:1px solid var(--line);
            border-radius:var(--radius); background:var(--surface); box-shadow:var(--shadow);
        }
        .report-ai-heading > span {
            display:block; color:#4A7FA7; font-size:.58rem; font-weight:800;
            letter-spacing:.13em; text-transform:uppercase; margin-bottom:.2rem;
        }
        .report-ai-heading h3 { color:var(--navy); font-size:1rem; margin:0; }
        .report-ai-heading p { color:var(--muted); font-size:.64rem; line-height:1.5; margin:.35rem 0 0; }
        .report-ai-meta {
            display:grid; grid-template-columns:1fr 1fr auto; align-items:center; gap:.8rem;
            margin-top:.9rem; padding-top:.8rem; border-top:1px solid #EDF0EF;
        }
        .report-ai-meta div span,.report-ai-meta div strong { display:block; }
        .report-ai-meta div span {
            color:#8A969C; font-size:.54rem; text-transform:uppercase; letter-spacing:.07em;
        }
        .report-ai-meta div strong { color:var(--ink); font-size:.64rem; margin-top:.15rem; }
        .report-ai-meta > b { padding:.32rem .55rem; border-radius:999px; font-size:.57rem; }
        .report-ai-meta > b.available { color:var(--positive); background:var(--accent-soft); }
        .report-ai-meta > b.unavailable { color:var(--muted); background:#EDF1F1; }
        @media (max-width: 650px) {
            .report-status { align-items:flex-start; }
            .report-ai-meta { grid-template-columns:1fr; }
            .report-ai-meta > b { justify-self:start; }
        }

        /* Batch workflow additions */
        .batch-stepper {
            display:flex; align-items:center; padding:.75rem 1rem; margin:.65rem 0 .9rem;
            border:1px solid var(--line); border-radius:11px; background:var(--surface);
        }
        .batch-stepper > i { flex:1; height:1px; margin:0 .9rem; background:var(--line); }
        .batch-step { display:flex; align-items:center; gap:.55rem; opacity:.45; }
        .batch-step.active { opacity:1; }
        .batch-step > b {
            display:grid; place-items:center; width:1.55rem; height:1.55rem; border-radius:50%;
            background:#EDF1F1; color:var(--muted); font-size:.58rem;
        }
        .batch-step.active > b { background:var(--navy); color:#FFF; }
        .batch-step span strong,.batch-step span small { display:block; white-space:nowrap; }
        .batch-step span strong { color:var(--ink); font-size:.64rem; }
        .batch-step span small { color:var(--muted); font-size:.53rem; margin-top:.1rem; }
        .batch-file-summary {
            display:flex; align-items:center; gap:.75rem; padding:.75rem .9rem; margin:.85rem 0;
            border:1px solid var(--line); border-radius:11px; background:var(--surface);
        }
        .batch-file-summary > div {
            display:grid; place-items:center; width:2.3rem; height:2.3rem; border-radius:8px;
            background:var(--accent-soft); color:var(--positive); font-size:.57rem; font-weight:800;
        }
        .batch-file-summary > span { flex:1; }
        .batch-file-summary span strong,.batch-file-summary span small { display:block; }
        .batch-file-summary span strong { color:var(--ink); font-size:.7rem; }
        .batch-file-summary span small { color:var(--muted); font-size:.56rem; margin-top:.15rem; }
        .batch-file-summary > b { color:var(--positive); font-size:.6rem; }
        @media (max-width: 650px) {
            .batch-stepper > i { margin:0 .35rem; }
            .batch-step span small { display:none; }
            .batch-file-summary { align-items:flex-start; flex-wrap:wrap; }
            .batch-file-summary > b { width:100%; margin-left:3.05rem; }
        }

        /* Project and privacy overview */
        .about-hero {
            display:grid; grid-template-columns:minmax(0,1.7fr) minmax(15rem,.7fr); gap:1rem;
            padding:1.45rem; margin:.25rem 0 1rem; border:1px solid var(--line);
            border-radius:14px; background:linear-gradient(135deg,#FFF 0%,#F5F8F7 100%);
        }
        .about-eyebrow { color:var(--positive); font-size:.55rem; font-weight:800; letter-spacing:.12em; }
        .about-hero h2 { max-width:44rem; margin:.42rem 0 .5rem; color:var(--ink); font-size:1.45rem; line-height:1.12; }
        .about-hero p,.about-grid p,.about-history p { margin:0; color:var(--muted); font-size:.66rem; line-height:1.65; }
        .about-hero aside { align-self:stretch; padding:1rem; border-radius:11px; background:var(--navy); color:#FFF; }
        .about-hero aside strong,.about-hero aside span { display:block; }
        .about-hero aside strong { margin-bottom:.45rem; font-size:.72rem; }
        .about-hero aside span { color:#C7D3D9; font-size:.61rem; line-height:1.55; }
        .about-section { padding:1.15rem 1.25rem; margin-bottom:1rem; border:1px solid var(--line); border-radius:14px; background:var(--surface); }
        .about-section h3,.about-grid h3,.about-privacy h3 { margin:.3rem 0 .7rem; color:var(--ink); font-size:.85rem; }
        .about-pipeline { display:flex; align-items:center; gap:.7rem; }
        .about-pipeline article { flex:1; min-height:5.2rem; padding:.8rem; border-radius:10px; background:#F4F7F6; }
        .about-pipeline article b,.about-pipeline article strong,.about-pipeline article span { display:block; }
        .about-pipeline article b { color:var(--positive); font-size:.55rem; }
        .about-pipeline article strong { margin:.25rem 0; color:var(--ink); font-size:.65rem; }
        .about-pipeline article span { color:var(--muted); font-size:.56rem; line-height:1.4; }
        .about-pipeline > i { color:#A4B2B7; font-style:normal; }
        .about-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:1rem; margin-bottom:1rem; }
        .about-grid article { padding:1.15rem 1.2rem; border:1px solid var(--line); border-radius:14px; background:var(--surface); }
        .about-card-icon { display:inline-block; padding:.27rem .42rem; border-radius:5px; background:var(--accent-soft); color:var(--positive); font-size:.5rem; font-weight:800; }
        .about-card-icon.external { background:#EEF0F8; color:#4A5E86; }
        .about-privacy { display:grid; grid-template-columns:8rem 1fr; gap:1rem; padding:1.2rem; margin-bottom:1rem; border-radius:14px; background:var(--navy); color:#FFF; }
        .about-privacy > div { color:#82D2B0; font-size:.55rem; font-weight:800; letter-spacing:.12em; }
        .about-privacy h3 { margin-top:0; color:#FFF; }
        .about-privacy p { margin:0; color:#CFD9DE; font-size:.63rem; line-height:1.65; }
        .about-method article { background:#FAFBFB; }
        .about-history { padding:.9rem 1rem; border-left:3px solid var(--positive); background:#F3F7F5; }
        .about-history strong { color:var(--ink); font-size:.64rem; }
        .about-history p { margin-top:.25rem; }
        @media (max-width: 760px) {
            .about-hero,.about-grid { grid-template-columns:1fr; }
            .about-pipeline { align-items:stretch; flex-direction:column; }
            .about-pipeline article { width:100%; min-height:0; }
            .about-pipeline > i { transform:rotate(90deg); }
            .about-privacy { grid-template-columns:1fr; gap:.45rem; }
        }

        /* Individual analysis workspace */
        .individual-intro {
            height:100%; min-height:13.4rem; padding:1.15rem 1.2rem;
            border:1px solid var(--line); border-radius:var(--radius); background:var(--surface);
            box-shadow:var(--shadow);
        }
        .individual-intro > span,.individual-result-heading > span {
            display:block; color:var(--positive); font-size:.58rem; font-weight:800;
            letter-spacing:.13em; text-transform:uppercase; margin-bottom:.25rem;
        }
        .individual-intro h3,.individual-result-heading h3 {
            color:var(--navy); font-size:1.05rem; margin:0; letter-spacing:-.025em;
        }
        .individual-intro > p { color:var(--muted); font-size:.68rem; line-height:1.55; margin:.6rem 0 1rem; }
        .individual-intro > div {
            display:flex; align-items:flex-start; gap:.5rem; padding:.7rem;
            border-radius:9px; background:var(--accent-soft); color:#416B5D;
        }
        .individual-intro > div i { color:var(--positive); font-style:normal; }
        .individual-intro > div small { font-size:.58rem; line-height:1.45; }
        .individual-empty {
            display:flex; align-items:center; justify-content:center; gap:.9rem; min-height:11rem;
            padding:1.5rem; margin-top:.9rem; border:1px dashed #BDC9C7;
            border-radius:var(--radius); background:rgba(255,255,255,.55);
        }
        .individual-empty > div {
            display:grid; place-items:center; flex:0 0 auto; width:2.8rem; height:2.8rem;
            border-radius:12px; background:var(--accent-soft); color:var(--positive); font-size:1.15rem;
        }
        .individual-empty strong { color:var(--navy); font-size:.8rem; }
        .individual-empty p { max-width:34rem; color:var(--muted); font-size:.62rem; line-height:1.5; margin:.25rem 0 0; }
        .individual-result-heading { margin:1.4rem 0 .8rem; }
        .individual-result-heading p { color:var(--muted); font-size:.64rem; margin:.28rem 0 0; }
        .individual-result-badges {
            display:flex; align-items:center; gap:.4rem; margin-bottom:.45rem; flex-wrap:wrap;
        }
        @media (max-width: 650px) {
            .individual-intro { min-height:auto; }
            .individual-empty { flex-direction:column; text-align:center; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
