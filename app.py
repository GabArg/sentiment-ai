"""Interfaz Streamlit para inferencia local de sentimiento.

Versión recuperada y modificada del proyecto grupal H12-25-L-Equipo-72.
Distribuida bajo GNU GPL v3.0. Consulte ATTRIBUTION.md y LICENSE.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

import joblib
import streamlit as st


APP_TITLE = "Sentiment AI"
PROJECT_DIR = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_DIR / "models" / "sentiment_model.joblib"
VECTORIZER_PATH = PROJECT_DIR / "models" / "tfidf_vectorizer.joblib"
MAX_TEXT_LENGTH = 5_000


st.set_page_config(
    page_title="Sentiment AI | Análisis de sentimientos",
    page_icon="◉",
    layout="centered",
    initial_sidebar_state="collapsed",
)


@st.cache_resource(show_spinner="Cargando modelo…")
def load_artifacts() -> tuple[Any, Any]:
    """Carga una única vez los artefactos versionados junto a la aplicación."""
    missing = [path.name for path in (MODEL_PATH, VECTORIZER_PATH) if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Faltan artefactos locales: {', '.join(missing)}")

    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)

    if not hasattr(model, "classes_") or not hasattr(model, "predict_proba"):
        raise TypeError("El clasificador no expone clases y probabilidades.")
    if not hasattr(vectorizer, "transform"):
        raise TypeError("El vectorizador no permite transformar texto.")
    return model, vectorizer


def predict_sentiment(text: str) -> tuple[str, float]:
    """Vectoriza el texto y devuelve la clase predicha y su probabilidad."""
    model, vectorizer = load_artifacts()
    features = vectorizer.transform([text])
    label = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0]
    class_index = list(model.classes_).index(label)
    return str(label), float(probabilities[class_index])


def sentiment_tone(label: str) -> tuple[str, str]:
    """Asigna una presentación sin alterar ni asumir las clases del modelo."""
    tones = {
        "positivo": ("#087F5B", "#E6FCF5"),
        "negativo": ("#C92A2A", "#FFF5F5"),
        "neutro": ("#364FC7", "#EDF2FF"),
    }
    return tones.get(label.casefold(), ("#343A40", "#F1F3F5"))


st.markdown(
    """
    <style>
    :root { --ink:#182230; --muted:#667085; --line:#E4E7EC; --accent:#3448C5; }
    .stApp {
        background:
          radial-gradient(circle at 8% 0%, rgba(52,72,197,.10), transparent 29rem),
          #F8FAFC;
    }
    .block-container { max-width: 780px; padding: 3.5rem 1.2rem 3rem; }
    .hero { margin-bottom: 1.7rem; }
    .eyebrow {
        color: var(--accent); font-size: .78rem; font-weight: 700;
        letter-spacing: .09em; text-transform: uppercase; margin-bottom: .65rem;
    }
    .hero h1 { color:var(--ink); font-size:clamp(2.4rem, 7vw, 4rem); line-height:1; letter-spacing:-.045em; margin:0; }
    .hero p { color:var(--muted); max-width:650px; font-size:1.05rem; line-height:1.65; margin:.9rem 0 0; }
    [data-testid="stTextArea"] textarea {
        min-height:190px; border-radius:14px; border:1px solid var(--line);
        background:#FFF; padding:1rem; line-height:1.55;
    }
    .stButton > button {
        width:100%; min-height:3rem; border:0; border-radius:10px;
        background:var(--accent); color:#FFF; font-weight:700;
    }
    .stButton > button:hover { background:#293BA8; color:#FFF; }
    .result-card {
        margin-top:1.2rem; padding:1.25rem 1.4rem; border-radius:14px;
        border:1px solid var(--result-color); background:var(--result-bg);
        display:grid; grid-template-columns:1fr auto; gap:1rem; align-items:center;
    }
    .result-label { color:var(--muted); font-size:.72rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; }
    .result-value { color:var(--result-color); font-size:clamp(1.65rem, 5vw, 2.2rem); font-weight:800; margin-top:.15rem; }
    .confidence { color:var(--ink); font-size:1.35rem; font-weight:800; text-align:right; }
    .details {
        margin-top:2.2rem; padding-top:1.35rem; border-top:1px solid var(--line);
        display:grid; grid-template-columns:1fr 1fr; gap:1.5rem;
    }
    .details h2 { color:var(--ink); font-size:.95rem; margin:0 0 .35rem; }
    .details p { color:var(--muted); font-size:.86rem; line-height:1.55; margin:0; }
    .legal { color:var(--muted); font-size:.76rem; line-height:1.5; margin-top:1.5rem; }
    @media (max-width: 560px) {
        .block-container { padding-top:2rem; }
        .details { grid-template-columns:1fr; gap:1rem; }
        .result-card { grid-template-columns:1fr; }
        .confidence { text-align:left; }
    }
    #MainMenu, footer { visibility:hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="hero">
      <div class="eyebrow">NLP · Machine Learning clásico</div>
      <h1>Sentiment AI</h1>
      <p>Demo de clasificación de opiniones mediante representación TF-IDF y
      regresión logística. El procesamiento ocurre localmente dentro de esta app.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

with st.form("sentiment_form", clear_on_submit=False):
    user_text = st.text_area(
        "Texto para analizar",
        placeholder="Ejemplo: La atención fue excelente y el envío llegó a tiempo.",
        max_chars=MAX_TEXT_LENGTH,
        help=f"Ingresá entre 2 y {MAX_TEXT_LENGTH:,} caracteres.",
    )
    submitted = st.form_submit_button("Analizar sentimiento", type="primary")

if submitted:
    clean_text = user_text.strip()
    if len(clean_text) < 2:
        st.warning("Ingresá un texto de al menos 2 caracteres.")
    else:
        try:
            predicted_label, confidence = predict_sentiment(clean_text)
            color, background = sentiment_tone(predicted_label)
            st.markdown(
                f"""
                <section class="result-card" style="--result-color:{color};--result-bg:{background}">
                  <div>
                    <div class="result-label">Sentimiento detectado</div>
                    <div class="result-value">{escape(predicted_label)}</div>
                  </div>
                  <div>
                    <div class="result-label">Probabilidad estimada</div>
                    <div class="confidence">{confidence:.1%}</div>
                  </div>
                </section>
                """,
                unsafe_allow_html=True,
            )
            st.caption("La probabilidad expresa la confianza interna del clasificador; no garantiza que la predicción sea correcta.")
        except (FileNotFoundError, TypeError, ValueError):
            st.error("La aplicación no pudo cargar artefactos de modelo válidos. Revisá la instalación del proyecto.")
        except Exception:
            st.error("No fue posible analizar el texto. Intentá nuevamente.")

st.markdown(
    """
    <section class="details">
      <div><h2>Cómo funciona</h2><p>El texto se convierte en un vector de unigramas y bigramas TF-IDF; una regresión logística asigna una de las clases aprendidas.</p></div>
      <div><h2>Tecnología</h2><p>Python · Streamlit · scikit-learn · joblib. Sin API separada, claves, descargas ni servicios externos en ejecución.</p></div>
    </section>
    <p class="legal">Versión recuperada, modificada y simplificada del proyecto grupal
    H12-25-L-Equipo-72. Distribuida bajo GPL-3.0; la autoría original del equipo se conserva en ATTRIBUTION.md.</p>
    """,
    unsafe_allow_html=True,
)
