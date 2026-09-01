"""Sentiment AI v2 — customer feedback analytics in Streamlit.

Recovered from team project H12-25-L-Equipo-72 and evolved for portfolio use.
See ATTRIBUTION.md and LICENSE (GPL-3.0).
"""

from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from src.ai_provider import DEFAULT_CEREBRAS_MODEL, generate_report_with_fallback
from src.analytics import calculate_metrics, sentiment_distribution
from src.batch import analyze_dataframe, analyze_dataframe_hybrid, estimate_hybrid_reviews
from src.hybrid import evaluate_hybrid_text
from src.hybrid_config import HybridRoutingConfig, load_hybrid_config
from src.model import SentimentPredictor
from src.pareto import calculate_pareto, extract_negative_topics
from src.preprocessing import CSVValidationError, read_csv_upload
from src.reporting import (
    estimate_payload,
    generate_deterministic_report,
    prepare_ai_context,
)
from src.sentiment_review import CerebrasSentimentReviewProvider


MAX_TEXT_LENGTH = 5_000
SENTIMENT_COLORS = {"Negativo": "#D92D20", "Neutro": "#475467", "Positivo": "#078A61"}
REVIEW_STATE_LABELS = {
    "local_only": "Modelo local",
    "reviewed": "Validado por second check",
    "disagreement": "Corregido por second check",
    "fallback_local": "Fallback local",
}

st.set_page_config(
    page_title="Sentiment AI v2 | Customer Feedback Analytics",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource(show_spinner="Cargando modelo local…")
def get_predictor() -> SentimentPredictor:
    return SentimentPredictor.load()


def get_hybrid_config() -> HybridRoutingConfig:
    return load_hybrid_config(st.secrets)


def get_batch_results() -> pd.DataFrame | None:
    value = st.session_state.get("batch_results")
    return value if isinstance(value, pd.DataFrame) and not value.empty else None


def get_analysis() -> tuple[pd.DataFrame, dict[str, object], pd.DataFrame]:
    results = get_batch_results()
    if results is None:
        raise ValueError("Primero procesá un CSV en Análisis masivo.")
    metrics = calculate_metrics(results)
    negative_texts = results.loc[results["sentiment"] == "Negativo", "text"].tolist()
    topics = extract_negative_topics(negative_texts)
    return results, metrics, calculate_pareto(topics)


def sentiment_probability_frame(probabilities: dict[str, float]) -> pd.DataFrame:
    return pd.DataFrame(
        {"sentiment": list(probabilities), "probability": list(probabilities.values())}
    )


def render_metric_cards(metrics: dict[str, object]) -> None:
    counts = metrics["counts"]
    cols = st.columns(5)
    cols[0].metric("Comentarios", f"{metrics['total']:,}")
    cols[1].metric("Positivos", f"{counts['Positivo']:,}", f"{metrics['percentages']['Positivo']:.1f}%")
    cols[2].metric("Neutros", f"{counts['Neutro']:,}", f"{metrics['percentages']['Neutro']:.1f}%")
    cols[3].metric("Negativos", f"{counts['Negativo']:,}", f"{metrics['percentages']['Negativo']:.1f}%", delta_color="inverse")
    cols[4].metric("Confianza media", f"{metrics['mean_confidence']:.1%}")


def render_individual() -> None:
    st.header("Análisis individual")
    st.write("Clasificá una opinión con el modelo local y revisá la probabilidad de cada clase aprendida.")
    with st.form("individual_form"):
        text = st.text_area(
            "Comentario",
            max_chars=MAX_TEXT_LENGTH,
            height=180,
            placeholder="Ejemplo: La atención fue excelente y el envío llegó a tiempo.",
        )
        submitted = st.form_submit_button("Analizar sentimiento", type="primary", width="stretch")
    if submitted:
        if len(text.strip()) < 2:
            st.warning("Ingresá un texto de al menos 2 caracteres.")
            return
        try:
            prediction = get_predictor().predict_one(text)
        except Exception:
            st.error("No fue posible analizar el texto con los artefactos locales.")
            return
        left, right = st.columns([1, 2])
        with left:
            st.metric("Resultado final", prediction.label)
            st.metric(
                "Confianza del modelo local",
                f"{prediction.confidence:.1%}",
                help="Estimación interna del clasificador local. No representa una garantía de corrección.",
            )
            st.caption("Origen: Modelo local")
        with right:
            st.subheader("Probabilidades del modelo local")
            chart_data = sentiment_probability_frame(prediction.probabilities)
            figure = px.bar(
                chart_data,
                x="probability",
                y="sentiment",
                orientation="h",
                color="sentiment",
                color_discrete_map=SENTIMENT_COLORS,
                text=chart_data["probability"].map(lambda value: f"{value:.1%}"),
                labels={"probability": "Probabilidad", "sentiment": ""},
            )
            figure.update_layout(showlegend=False, height=280, margin=dict(l=0, r=10, t=10, b=0))
            figure.update_xaxes(tickformat=".0%", range=[0, 1])
            st.plotly_chart(figure, use_container_width=True)
        st.caption("La confianza mostrada es una estimación interna del modelo local, no una garantía de corrección.")


def render_batch() -> None:
    st.header("Análisis masivo")
    st.write("Subí un CSV, elegí la columna de comentarios y ejecutá inferencia vectorizada.")
    uploaded = st.file_uploader("Archivo CSV", type=["csv"], help="Máximo 10 MB y 10.000 filas.")
    if uploaded is None:
        st.info("El archivo se procesa localmente en la sesión de Streamlit y no se envía a Cerebras.")
        return
    try:
        frame = read_csv_upload(uploaded.getvalue())
    except CSVValidationError as exc:
        st.error(str(exc))
        return
    st.success(f"CSV válido: {len(frame):,} registros y {len(frame.columns)} columnas detectadas.")
    st.dataframe(frame.head(20), width="stretch", hide_index=True)
    column = st.selectbox("Columna que contiene el comentario", options=list(frame.columns))
    if st.button("Procesar comentarios", type="primary", width="stretch"):
        try:
            with st.spinner("Vectorizando y clasificando el lote…"):
                results, dropped = analyze_dataframe(frame, column, get_predictor())
            st.session_state["batch_results"] = results
            st.session_state.pop("ai_report", None)
            st.success(f"Se analizaron {len(results):,} comentarios. Se omitieron {dropped:,} valores nulos o vacíos.")
        except (CSVValidationError, ValueError) as exc:
            st.error(str(exc))
        except Exception:
            st.error("No fue posible completar el análisis masivo.")
    results = get_batch_results()
    if results is not None:
        st.subheader("Resultados procesados")
        display = results.copy()
        percentage_columns = [column for column in display if column.startswith("probability_")]
        display["confidence"] = display["confidence"].map(lambda value: f"{value:.1%}")
        for probability_column in percentage_columns:
            display[probability_column] = display[probability_column].map(lambda value: f"{value:.1%}")
        st.dataframe(display.head(100), width="stretch", hide_index=True)
        csv_data = results.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Descargar CSV procesado",
            data=csv_data,
            file_name="sentiment_analysis_results.csv",
            mime="text/csv",
            width="stretch",
        )


def render_individual_controlled() -> None:
    config = get_hybrid_config()
    if not config.enabled:
        render_individual()
        return
    st.header("Análisis individual")
    st.write("La clasificación local ocurre primero. Los casos derivados pueden recibir un second check externo anonimizado.")
    with st.form("individual_form"):
        text = st.text_area("Comentario", max_chars=MAX_TEXT_LENGTH, height=180)
        submitted = st.form_submit_button("Analizar sentimiento", type="primary", width="stretch")
    if not submitted:
        return
    if len(text.strip()) < 2:
        st.warning("Ingresá un texto de al menos 2 caracteres.")
        return
    try:
        predictor = get_predictor()
        prediction = predictor.predict_one(text)
        result = evaluate_hybrid_text(
            text,
            predictor,
            config=config.router_config(),
            provider=CerebrasSentimentReviewProvider(
                api_key=_streamlit_cerebras_key(),
                max_retries=0,
            ),
        )
    except Exception:
        st.error("No fue posible analizar el texto con los artefactos locales.")
        return
    left, right = st.columns([1, 2])
    with left:
        st.metric("Resultado final", result.final_prediction)
        st.metric(
            "Confianza del modelo local",
            f"{prediction.confidence:.1%}",
            help="Estimación interna del clasificador local. No representa la confianza del resultado híbrido.",
        )
        if result.review_state in {"reviewed", "disagreement"}:
            origin = "Revisión híbrida"
        elif result.review_state == "fallback_local":
            origin = "Fallback local"
        else:
            origin = "Modelo local"
        st.caption(f"Origen: {origin}")
        st.markdown(f"**Estado:** {REVIEW_STATE_LABELS[result.review_state]}")
    with right:
        st.subheader("Probabilidades del modelo local")
        st.caption("Distribución previa al second check")
        chart_data = sentiment_probability_frame(prediction.probabilities)
        figure = px.bar(
            chart_data,
            x="probability",
            y="sentiment",
            orientation="h",
            color="sentiment",
            color_discrete_map=SENTIMENT_COLORS,
            text=chart_data["probability"].map(lambda value: f"{value:.1%}"),
            labels={"probability": "Probabilidad local", "sentiment": ""},
        )
        figure.update_layout(showlegend=False, height=280, margin=dict(l=0, r=10, t=10, b=0))
        figure.update_xaxes(tickformat=".0%", range=[0, 1])
        st.plotly_chart(figure, use_container_width=True)
    st.caption("La confianza mostrada es una estimación interna del modelo local; no representa confianza del resultado híbrido.")
    if result.review_state == "disagreement":
        st.info("El second check modificó la clasificación inicial.")
    elif result.review_state == "reviewed":
        st.success("El second check confirmó la clasificación local.")
    elif result.review_state == "fallback_local":
        st.warning("La revisión externa no estuvo disponible; se conserva la clasificación local.")
    with st.expander("Detalle de revisión"):
        st.write(f"Predicción local: **{result.local_prediction}**")
        st.write(f"Confianza local: **{result.local_confidence:.1%}**")
        if result.review_state == "local_only":
            st.write("Este caso no alcanzó los criterios de revisión externa.")
        elif result.review_reasons:
            st.write("Motivo de revisión: **baja confianza local**")
            st.caption(f"Regla técnica: {', '.join(result.review_reasons)}")
        if result.review_prediction:
            st.write(f"Second check: **{result.review_prediction}**")
        if result.review_latency_ms is not None:
            st.write(f"Latencia externa: **{result.review_latency_ms:.0f} ms**")


def render_batch_controlled() -> None:
    config = get_hybrid_config()
    if not config.enabled:
        render_batch()
        return
    st.header("Análisis masivo")
    st.write("La clasificación local ocurre primero; sólo los casos derivados reciben un second check controlado.")
    uploaded = st.file_uploader("Archivo CSV", type=["csv"], help="Máximo 10 MB y 10.000 filas.")
    if uploaded is None:
        st.info("Sólo comentarios derivados pueden enviarse a Cerebras tras anonimizar emails, teléfonos, URLs e IDs largos. No se envían otras columnas del CSV.")
        return
    try:
        frame = read_csv_upload(uploaded.getvalue())
    except CSVValidationError as exc:
        st.error(str(exc))
        return
    st.success(f"CSV válido: {len(frame):,} registros y {len(frame.columns)} columnas detectadas.")
    st.dataframe(frame.head(20), width="stretch", hide_index=True)
    column = st.selectbox("Columna que contiene el comentario", options=list(frame.columns))
    try:
        requested, allowed, _ = estimate_hybrid_reviews(frame, column, get_predictor(), config)
        st.info(
            f"Revisiones previstas: {requested:,}. Máximo a ejecutar: {allowed:,}. "
            f"Costo orientativo observado: ~USD {allowed * config.estimated_review_cost_usd:.4f}. "
            "Es una estimación; el costo real depende de tokens, modelo y precios."
        )
    except (CSVValidationError, ValueError):
        requested = allowed = 0
    if st.button("Procesar comentarios", type="primary", width="stretch"):
        try:
            progress = st.progress(0, text="La clasificación local se ejecuta primero…")
            pacing_status = st.empty()

            def on_progress(current, total):
                progress.progress(current / max(total, 1), text=f"Revisando con IA {current} de {total}")

            def on_pacing(_wait):
                pacing_status.info("Esperando ventana de Cerebras para continuar…")

            results, dropped, summary = analyze_dataframe_hybrid(
                frame,
                column,
                get_predictor(),
                CerebrasSentimentReviewProvider(api_key=_streamlit_cerebras_key(), max_retries=1),
                config,
                on_progress=on_progress,
                on_pacing=on_pacing,
            )
            progress.empty()
            pacing_status.empty()
            st.session_state["batch_results"] = results
            st.session_state["hybrid_summary"] = summary
            st.session_state.pop("ai_report", None)
            st.success(f"Se analizaron {len(results):,} comentarios. Se omitieron {dropped:,} valores nulos o vacíos.")
            if summary["review_budget_exceeded"]:
                st.warning(f"{summary['review_budget_exceeded']:,} comentarios adicionales conservaron la clasificación local por límite de revisión IA.")
        except (CSVValidationError, ValueError) as exc:
            st.error(str(exc))
        except Exception:
            st.error("No fue posible completar el análisis masivo.")
    results = get_batch_results()
    if results is not None:
        st.subheader("Resultados procesados")
        display = results.copy()
        if "review_state" in display:
            display["review_state"] = display["review_state"].map(REVIEW_STATE_LABELS).fillna("Estado desconocido")
        percentage_columns = [name for name in display if name.startswith("probability_")]
        for name in ["confidence", "local_confidence"]:
            if name in display:
                display[name] = display[name].map(lambda value: f"{value:.1%}")
        for name in percentage_columns:
            display[name] = display[name].map(lambda value: f"{value:.1%}")
        display = display.rename(columns={"review_state": "Estado de revisión"})
        st.dataframe(display.head(100), width="stretch", hide_index=True)
        summary = st.session_state.get("hybrid_summary")
        if isinstance(summary, dict):
            st.caption(
                f"Trazabilidad: Modelo local {summary['local_only']:,} · "
                f"Confirmados por second check {summary['reviewed']:,} · "
                f"Corregidos por second check {summary['disagreement']:,} · "
                f"Fallback local {summary['fallback']:,}"
            )
        st.download_button(
            "Descargar CSV procesado",
            data=results.to_csv(index=False).encode("utf-8-sig"),
            file_name="sentiment_analysis_results.csv",
            mime="text/csv",
            width="stretch",
        )


def render_dashboard() -> None:
    st.header("Dashboard")
    try:
        results, metrics, _ = get_analysis()
    except ValueError as exc:
        st.info(str(exc))
        return
    render_metric_cards(metrics)
    if "review_state" in results.columns:
        states = results["review_state"].value_counts(normalize=True).mul(100)
        dashboard_labels = {
            "local_only": "Modelo local",
            "reviewed": "Confirmados por second check",
            "disagreement": "Corregidos por second check",
            "fallback_local": "Fallback local",
        }
        st.caption(
            "Trazabilidad híbrida: "
            + " · ".join(
                f"{dashboard_labels.get(state, 'Estado desconocido')} {value:.1f}%"
                for state, value in states.items()
            )
        )
    distribution = sentiment_distribution(metrics)
    left, right = st.columns(2)
    with left:
        figure = px.bar(
            distribution,
            x="sentiment",
            y="count",
            color="sentiment",
            color_discrete_map=SENTIMENT_COLORS,
            text="count",
            labels={"sentiment": "Sentimiento", "count": "Comentarios"},
            title="Distribución de sentimientos",
        )
        figure.update_layout(showlegend=False, margin=dict(l=0, r=0, t=50, b=0))
        st.plotly_chart(figure, use_container_width=True)
    with right:
        confidence = results.groupby("sentiment", as_index=False)["confidence"].mean()
        figure = px.bar(
            confidence,
            x="sentiment",
            y="confidence",
            color="sentiment",
            color_discrete_map=SENTIMENT_COLORS,
            text=confidence["confidence"].map(lambda value: f"{value:.1%}"),
            labels={"sentiment": "Sentimiento", "confidence": "Confianza media"},
            title="Confianza media por clase",
        )
        figure.update_yaxes(tickformat=".0%", range=[0, 1])
        figure.update_layout(showlegend=False, margin=dict(l=0, r=0, t=50, b=0))
        st.plotly_chart(figure, use_container_width=True)

    st.subheader("Visión de negocio")
    negative_pct = metrics["percentages"]["Negativo"]
    positive_pct = metrics["percentages"]["Positivo"]
    ratio = metrics["positive_negative_ratio"]
    business_cols = st.columns(3)
    business_cols[0].metric("Feedback negativo", f"{negative_pct:.1f}%")
    business_cols[1].metric("Señal positiva", f"{positive_pct:.1f}%")
    business_cols[2].metric(
        "Ratio positivo/negativo",
        "Sin negativos" if ratio == float("inf") else f"{ratio:.2f}",
    )
    st.write(
        f"Se detectaron **{metrics['critical_negative_count']:,} comentarios negativos críticos**, definidos de forma transparente como negativos cuya confianza está en el cuartil superior del lote (≥ {metrics['critical_confidence_threshold']:.1%})."
    )


def render_pareto() -> None:
    st.header("Pareto de feedback negativo")
    st.write("Los temas son n-gramas presentes en comentarios negativos. Se cuentan una vez por comentario para evitar que la repetición dentro de un texto infle la frecuencia.")
    try:
        _, _, pareto = get_analysis()
    except ValueError as exc:
        st.info(str(exc))
        return
    if pareto.empty:
        st.info("No hay suficientes comentarios negativos para extraer temas.")
        return
    display = pareto.copy()
    display["percentage"] = display["percentage"].map(lambda value: f"{value:.1f}%")
    display["cumulative_percentage"] = display["cumulative_percentage"].map(lambda value: f"{value:.1f}%")
    display["within_80_percent"] = display["within_80_percent"].map({True: "Sí", False: "No"})
    display.columns = ["Tema", "Frecuencia", "Porcentaje", "Acumulado", "Dentro del 80%"]
    st.dataframe(display, width="stretch", hide_index=True)

    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_trace(go.Bar(x=pareto["topic"], y=pareto["frequency"], name="Frecuencia", marker_color="#3448C5"), secondary_y=False)
    figure.add_trace(go.Scatter(x=pareto["topic"], y=pareto["cumulative_percentage"], name="% acumulado", mode="lines+markers", line=dict(color="#D92D20", width=3)), secondary_y=True)
    figure.add_hline(y=80, line_dash="dash", line_color="#667085", annotation_text="80%", secondary_y=True)
    figure.update_yaxes(title_text="Frecuencia", secondary_y=False)
    figure.update_yaxes(title_text="Porcentaje acumulado", range=[0, 105], ticksuffix="%", secondary_y=True)
    figure.update_layout(height=520, margin=dict(l=0, r=0, t=30, b=0), xaxis_tickangle=-35)
    st.plotly_chart(figure, use_container_width=True)


def _streamlit_cerebras_key() -> str | None:
    try:
        return st.secrets.get("CEREBRAS_API_KEY") or os.getenv("CEREBRAS_API_KEY")
    except Exception:
        return os.getenv("CEREBRAS_API_KEY")


def render_report() -> None:
    st.header("Informe ejecutivo")
    try:
        _, metrics, pareto = get_analysis()
    except ValueError as exc:
        st.info(str(exc))
        return
    deterministic = generate_deterministic_report(metrics, pareto)
    st.subheader("Informe generado sin IA")
    st.markdown(deterministic)
    st.download_button(
        "Descargar informe determinístico",
        data=deterministic.encode("utf-8"),
        file_name="executive_sentiment_report.md",
        mime="text/markdown",
        width="stretch",
    )

    st.divider()
    st.subheader("Informe IA opcional con Cerebras")
    st.write(f"Modelo: `{DEFAULT_CEREBRAS_MODEL}`. La llamada ocurre sólo al pulsar el botón y nunca recibe el CSV completo.")
    context = prepare_ai_context(metrics, pareto)
    size = estimate_payload(context)
    st.caption(f"Payload estimado: {size['characters']:,} caracteres (~{size['approximate_tokens']:,} tokens), más el prompt versionado.")
    key = _streamlit_cerebras_key()
    if not key:
        st.info("CEREBRAS_API_KEY no está configurada. El informe determinístico permanece disponible.")
    if st.button("Generar informe con IA", disabled=not bool(key), type="primary", width="stretch"):
        with st.spinner("Generando informe agregado con Cerebras…"):
            report, used_ai, error = generate_report_with_fallback(
                deterministic,
                context,
                api_key=key,
            )
        st.session_state["ai_report"] = report
        st.session_state["ai_report_used_ai"] = used_ai
        if error:
            st.warning("Cerebras no respondió correctamente. Se muestra el informe ejecutivo generado sin IA.")
    if "ai_report" in st.session_state:
        label = "Informe generado con IA" if st.session_state.get("ai_report_used_ai") else "Informe ejecutivo generado sin IA"
        st.subheader(label)
        st.markdown(st.session_state["ai_report"])
        st.download_button(
            "Descargar informe mostrado",
            data=st.session_state["ai_report"].encode("utf-8"),
            file_name="ai_business_insights.md",
            mime="text/markdown",
            width="stretch",
        )


def render_about() -> None:
    hybrid_enabled = get_hybrid_config().enabled
    st.header("Acerca del proyecto")
    st.markdown(
        """
        **Sentiment AI v2** combina NLP clásico reproducible con analítica de feedback y un informe generativo opcional.

        - **Proyecto original:** desarrollo grupal H12-25-L-Equipo-72 de No Country.
        - **Recuperación V6:** TF-IDF, regresión logística ternaria y artefactos originales empaquetados localmente.
        - **Evolución v2:** nueva implementación modular de batch CSV, dashboard, Pareto e informes para portfolio.

        Esta v2 se inspira funcionalmente en la aplicación histórica posterior, cuyo código no está disponible; no afirma reconstruir ese código. La atribución completa y las contribuciones verificables están en `ATTRIBUTION.md`.
        """
    )
    st.subheader("Privacidad")
    if hybrid_enabled:
        st.write("La clasificación local ocurre primero. Sólo comentarios derivados pueden enviarse anonimizados a Cerebras para second check; nunca se envían otras columnas del CSV. El informe IA permanece separado y sólo recibe agregados.")
    else:
        st.write("La clasificación y el dashboard son locales. Cerebras sólo recibe métricas y frecuencias agregadas; las etiquetas textuales de los temas también se excluyen. Nunca se envían comentarios, el CSV ni sus otras columnas.")


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

with st.sidebar:
    st.markdown('<div class="product-label">Customer Feedback Analytics</div>', unsafe_allow_html=True)
    st.title("Sentiment AI v2")
    st.markdown('<p class="product-copy">TF-IDF + regresión logística + analítica de negocio + informe IA opcional.</p>', unsafe_allow_html=True)
    page = st.radio(
        "Navegación",
        ["Análisis individual", "Análisis masivo", "Dashboard", "Pareto 80/20", "Informe", "Acerca del proyecto"],
        label_visibility="collapsed",
    )
    if get_batch_results() is not None:
        st.success(f"Lote activo: {len(get_batch_results()):,} comentarios")

pages = {
    "Análisis individual": render_individual_controlled,
    "Análisis masivo": render_batch_controlled,
    "Dashboard": render_dashboard,
    "Pareto 80/20": render_pareto,
    "Informe": render_report,
    "Acerca del proyecto": render_about,
}
pages[page]()
