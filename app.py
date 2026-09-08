"""Sentiment AI v2 — customer feedback analytics in Streamlit.

Recovered from team project H12-25-L-Equipo-72 and evolved for portfolio use.
See ATTRIBUTION.md and LICENSE (GPL-3.0).
"""

from __future__ import annotations

import os

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from src.ai_provider import DEFAULT_CEREBRAS_MODEL, generate_report_with_fallback
from src.analytics import calculate_metrics, sentiment_distribution
from src.batch import (
    analyze_dataframe,
    analyze_dataframe_hybrid,
    analyze_dataframe_multilingual,
    analyze_dataframe_direct_multilingual,
    estimate_hybrid_reviews,
    estimate_multilingual_translations,
)
from src.external_requests import ExternalRequestCoordinator
from src.direct_multilingual import evaluate_direct_multilingual
from src.direct_review_config import load_direct_review_config
from src.hybrid import evaluate_hybrid_text
from src.hybrid_config import HybridRoutingConfig, load_hybrid_config
from src.language_detection import LocalLanguageDetector
from src.model import SentimentPredictor
from src.multilingual_config import MultilingualConfig, load_multilingual_config
from src.multilingual_pipeline import evaluate_multilingual_sentiment
from src.pareto import calculate_pareto, extract_negative_topics
from src.preprocessing import CSVValidationError, read_csv_upload
from src.reporting import (
    estimate_payload,
    generate_deterministic_report,
    prepare_ai_context,
)
from src.sentiment_review import CerebrasSentimentReviewProvider
from src.rate_pacer import RatePacer
from src.translation import CerebrasTranslationProvider
from src.structured_sentiment_review import StructuredSentimentReviewProvider
from src.ui import (
    build_dashboard_view_model,
    build_traceability_text,
    format_navigation_label,
    load_global_styles,
    render_batch_csv_preview,
    render_batch_kpi_cards,
    render_batch_results_header,
    render_batch_summary_band,
    render_batch_upload_empty,
    render_attention_panel,
    render_confidence_context_chart,
    render_dashboard_kpis,
    render_dataset_reading,
    render_panel_heading,
    render_probability_chart,
    render_sentiment_distribution_chart,
    render_dataset_context,
    render_page_header,
    render_result_card,
    render_sidebar_brand,
    render_sidebar_signature,
    render_workspace_empty_state,
)
from src.ui.charts import SENTIMENT_COLORS, apply_plotly_theme


MAX_TEXT_LENGTH = 5_000
REVIEW_STATE_LABELS = {
    "local_only": "Modelo local",
    "reviewed": "Validado por second check",
    "disagreement": "Corregido por second check",
    "fallback_local": "Fallback local",
}
LANGUAGE_NAMES = {"es": "Español", "en": "Inglés", "pt": "Portugués", "it": "Italiano"}
TRANSLATION_STATE_LABELS = {
    "not_needed": "No necesaria",
    "translated": "Aplicada",
    "fallback_original": "Fallback al original",
    "unsupported_language": "Idioma no soportado",
    "detection_error": "Error de detección",
}
DIRECT_REVIEW_STATE_LABELS = {
    "local_only": "Modelo local",
    "direct_multilingual_review": "Revisión multilingüe directa",
    "direct_review_failed": "Fallback local",
}
EXTERNAL_ERROR_LABELS = {
    "external_budget_exceeded": "Límite de llamadas externas alcanzado",
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


def get_multilingual_config() -> MultilingualConfig:
    return load_multilingual_config(st.secrets)

def get_direct_review_config():
    return load_direct_review_config(st.secrets)


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
    st.write("Clasificá una opinión con el modelo local y revisá la probabilidad de cada clase aprendida.")
    st.caption("Procesamiento local-first: inferencia determinística en la sesión con modelo empaquetado.")
    with st.form("individual_form"):
        text = st.text_area(
            "Comentario",
            max_chars=MAX_TEXT_LENGTH,
            height=160,
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
        left, right = st.columns([1, 1.2])
        with left:
            render_result_card(
                prediction.label,
                prediction.confidence,
                "Modelo local",
                confidence_help="Estimación interna del clasificador local. No representa una garantía de corrección.",
            )
        with right:
            st.subheader("Probabilidades del modelo local")
            render_probability_chart(prediction.probabilities)
        st.caption("La confianza mostrada es una estimación interna del modelo local, no una garantía de corrección.")
        with st.expander("Traza técnica"):
            st.write(f"Predicción local: **{prediction.label}**")
            st.write(f"Confianza local: **{prediction.confidence:.1%}**")
            st.write("Origen: **Modelo local**")


def render_batch() -> None:
    st.markdown("Subí un CSV, elegí la columna de comentarios y ejecutá inferencia vectorizada.")
    uploaded = st.file_uploader("Archivo CSV", type=["csv"], help="Máximo 10 MB y 10.000 filas.")
    if uploaded is None:
        render_batch_upload_empty(
            "El archivo se procesa localmente en la sesión de Streamlit y no se envía a Cerebras."
        )
        st.info("El archivo se procesa localmente en la sesión de Streamlit y no se envía a Cerebras.")
        return
    try:
        frame = read_csv_upload(uploaded.getvalue())
    except CSVValidationError as exc:
        st.error(str(exc))
        return
    column = st.selectbox("Columna que contiene el comentario", options=list(frame.columns))
    render_batch_csv_preview(len(frame), len(frame.columns), column)
    st.dataframe(frame.head(20), width="stretch", hide_index=True)
    if st.button("Procesar comentarios", type="primary", width="stretch"):
        try:
            with st.spinner("Vectorizando y clasificando el lote…"):
                results, dropped = analyze_dataframe(frame, column, get_predictor())
            st.session_state["batch_results"] = results
            st.session_state.pop("ai_report", None)
            render_batch_summary_band(len(results), dropped)
        except (CSVValidationError, ValueError) as exc:
            st.error(str(exc))
        except Exception:
            st.error("No fue posible completar el análisis masivo.")
    results = get_batch_results()
    if results is not None:
        render_batch_results_header()
        metrics = calculate_metrics(results)
        render_batch_kpi_cards(metrics)
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
    multilingual = get_multilingual_config()
    direct_config = get_direct_review_config()
    if not config.enabled and not multilingual.enabled and not direct_config.enabled:
        render_individual()
        return
    if direct_config.enabled:
        st.write("Los textos no españoles o breves pueden recibir una revisión multilingüe directa sobre el comentario anonimizado.")
    elif multilingual.enabled:
        st.write("El idioma se detecta localmente. Los textos que requieren traducción se anonimizan antes de enviarse al proveedor externo.")
        st.caption("La detección puede ser menos fiable en textos breves o ambiguos.")
    else:
        st.write("La clasificación local ocurre primero. Los casos derivados pueden recibir un second check externo anonimizado.")
    st.caption("Procesamiento local-first: la inferencia inicial siempre se evalúa localmente.")
    with st.form("individual_form"):
        text = st.text_area(
            "Comentario",
            max_chars=MAX_TEXT_LENGTH,
            height=160,
            placeholder="Ejemplo: La atención fue excelente y el envío llegó a tiempo.",
        )
        submitted = st.form_submit_button("Analizar sentimiento", type="primary", width="stretch")
    if not submitted:
        return
    if len(text.strip()) < 2:
        st.warning("Ingresá un texto de al menos 2 caracteres.")
        return
    try:
        predictor = get_predictor()
        direct_result = None
        if direct_config.enabled:
            coordinator = ExternalRequestCoordinator(multilingual.max_external_calls_per_batch, RatePacer(config.max_requests, config.window_seconds, config.pacing_margin_seconds))
            direct_result = evaluate_direct_multilingual(text,predictor,LocalLanguageDetector(),StructuredSentimentReviewProvider(api_key=_streamlit_cerebras_key(),max_retries=0),coordinator,config,CerebrasSentimentReviewProvider(api_key=_streamlit_cerebras_key(),max_retries=0) if config.enabled else None)
            prediction=predictor.predict_one(text);preparation=None;result=direct_result.hybrid
        elif multilingual.enabled:
            coordinator = ExternalRequestCoordinator(
                multilingual.max_external_calls_per_batch,
                RatePacer(config.max_requests, config.window_seconds, config.pacing_margin_seconds),
            )
            combined = evaluate_multilingual_sentiment(
                text,
                predictor,
                True,
                LocalLanguageDetector(),
                CerebrasTranslationProvider(api_key=_streamlit_cerebras_key(), max_retries=0),
                config,
                CerebrasSentimentReviewProvider(api_key=_streamlit_cerebras_key(), max_retries=0)
                if config.enabled else None,
                coordinator,
            )
            result = combined.sentiment
            preparation = combined.preparation
            prediction = predictor.predict_one(preparation.analysis_text)
        else:
            preparation = None
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
    if direct_result is not None and direct_result.direct_review_requested:
        left, right = st.columns([1, 1.2])
        with left:
            origin = "Revisión multilingüe directa" if direct_result.direct_review_state == "direct_multilingual_review" else "Fallback local"
            render_result_card(
                direct_result.final_prediction,
                prediction.confidence,
                origin,
                confidence_help="Estimación interna del clasificador local; no representa la confianza de la revisión externa.",
            )
            if direct_result.language_state == "short_text_uncertain":
                st.markdown("**Idioma:** Idioma incierto por texto breve")
            else:
                st.markdown(f"**Idioma detectado:** {direct_result.language_name or direct_result.detected_language or 'No determinado'}")
            if direct_result.direct_review_state == "direct_multilingual_review":
                st.success("La clasificación proviene de una revisión multilingüe directa.")
                st.caption("Para esta revisión se envió únicamente el comentario anonimizado.")
            else:
                st.warning("Revisión externa no disponible; se utilizó el fallback local.")
        with right:
            st.subheader("Probabilidades del modelo local")
            render_probability_chart(prediction.probabilities, probability_label="Probabilidad local")
        with st.expander("Detalle técnico de revisión"):
            st.write(f"Predicción local: **{prediction.label}**")
            st.write(f"Confianza local: **{prediction.confidence:.1%}**")
            st.write(f"Estado directo: **{direct_result.direct_review_state}**")
            if direct_result.direct_review_latency_ms is not None:
                st.write(f"Latencia externa: **{direct_result.direct_review_latency_ms:.0f} ms**")
        return
    left, right = st.columns([1, 1.2])
    with left:
        if result.review_state in {"reviewed", "disagreement"}:
            origin = "Revisión híbrida"
        elif result.review_state == "fallback_local":
            origin = "Fallback local"
        else:
            origin = "Modelo local"
        render_result_card(
            result.final_prediction,
            prediction.confidence,
            origin,
            confidence_help="Estimación interna del clasificador local. No representa la confianza del resultado híbrido.",
            state_label=REVIEW_STATE_LABELS[result.review_state],
        )
        if result.review_state == "disagreement":
            st.info("El second check modificó la clasificación inicial.")
        elif result.review_state == "reviewed":
            st.success("El second check confirmó la clasificación local.")
        elif result.review_state == "fallback_local":
            st.warning("La revisión externa no estuvo disponible; se conserva la clasificación local.")
    with right:
        st.subheader("Probabilidades del modelo local")
        st.caption("Distribución previa al second check")
        render_probability_chart(prediction.probabilities, probability_label="Probabilidad local")
    st.caption("La confianza mostrada es una estimación interna del modelo local; no representa confianza del resultado híbrido.")
    if preparation is not None:
        language_label = preparation.language_name or preparation.detected_language or "No determinado"
        st.markdown(f"**Idioma detectado:** {language_label}")
        st.markdown(f"**Traducción:** {TRANSLATION_STATE_LABELS[preparation.translation_state]}")
        if preparation.translation_state == "translated":
            with st.expander("Texto usado para análisis"):
                st.caption("Traducción utilizada para el análisis; no es el texto original.")
                st.write(preparation.translated_text)
        elif preparation.translation_state == "fallback_original":
            if preparation.translation_error_code == "external_budget_exceeded":
                st.warning("Límite de llamadas externas alcanzado; el análisis continuó con el texto original.")
            else:
                st.warning("La traducción externa no estuvo disponible; el análisis continuó con el texto original.")
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
    multilingual = get_multilingual_config()
    direct_config=get_direct_review_config()
    if not config.enabled and not multilingual.enabled and not direct_config.enabled:
        render_batch()
        return
    if direct_config.enabled:
        st.markdown("Los textos no españoles o breves usan revisión multilingüe directa; no se traducen.")
    elif multilingual.enabled:
        st.markdown("La detección local y la traducción controlada ocurren antes del análisis de sentimiento.")
    else:
        st.markdown("La clasificación local ocurre primero; sólo los casos derivados reciben un second check controlado.")
    uploaded = st.file_uploader("Archivo CSV", type=["csv"], help="Máximo 10 MB y 10.000 filas.")
    if uploaded is None:
        if direct_config.enabled:
            privacy_msg = "Sólo se envía el comentario anonimizado para las revisiones directas; no se envían otras columnas del CSV."
        elif multilingual.enabled:
            privacy_msg = "Los textos que requieren traducción se anonimizan antes de enviarse a Cerebras. Sólo se envía el comentario anonimizado, sin otras columnas; el original queda preservado en la app."
        else:
            privacy_msg = "Sólo comentarios derivados pueden enviarse a Cerebras tras anonimizar emails, teléfonos, URLs e IDs largos. No se envían otras columnas del CSV."
        render_batch_upload_empty(privacy_msg)
        st.info(privacy_msg)
        return
    try:
        frame = read_csv_upload(uploaded.getvalue())
    except CSVValidationError as exc:
        st.error(str(exc))
        return
    column = st.selectbox("Columna que contiene el comentario", options=list(frame.columns))
    render_batch_csv_preview(len(frame), len(frame.columns), column)
    st.dataframe(frame.head(20), width="stretch", hide_index=True)
    try:
        if direct_config.enabled:
            st.info(f"Límite total compartido de llamadas externas: {multilingual.max_external_calls_per_batch:,}. Las rutas directas consumen una llamada.")
        elif multilingual.enabled:
            translations, _ = estimate_multilingual_translations(frame, column, LocalLanguageDetector())
            review_note = "Los second checks se determinan después de traducir y clasificar." if config.enabled else "Second checks desactivados."
            st.info(
                f"Traducciones previstas: {translations:,}. Límite total de llamadas externas: "
                f"{multilingual.max_external_calls_per_batch:,}. {review_note}"
            )
        else:
            requested, allowed, _ = estimate_hybrid_reviews(frame, column, get_predictor(), config)
            st.info(
                f"Revisiones previstas: {requested:,}. Máximo a ejecutar: {allowed:,}. "
                f"Costo orientativo observado: ~USD {allowed * config.estimated_review_cost_usd:.4f}. "
                "Es una estimación; el costo real depende de tokens, modelo y precios."
            )
    except (CSVValidationError, ValueError):
        pass
    if st.button("Procesar comentarios", type="primary", width="stretch"):
        try:
            progress = st.progress(0, text="La clasificación local se ejecuta primero…")
            pacing_status = st.empty()

            def on_progress(current, total):
                label = "Procesando flujo multilenguaje" if multilingual.enabled else "Revisando con IA"
                progress.progress(current / max(total, 1), text=f"{label} {current} de {total}")

            def on_pacing(_wait):
                pacing_status.info("Esperando ventana de Cerebras para continuar…")

            if direct_config.enabled:
                coordinator=ExternalRequestCoordinator(multilingual.max_external_calls_per_batch,RatePacer(config.max_requests,config.window_seconds,config.pacing_margin_seconds),on_pacing)
                results,dropped,summary=analyze_dataframe_direct_multilingual(frame,column,get_predictor(),LocalLanguageDetector(),StructuredSentimentReviewProvider(api_key=_streamlit_cerebras_key(),max_retries=1),coordinator,config,CerebrasSentimentReviewProvider(api_key=_streamlit_cerebras_key(),max_retries=1) if config.enabled else None,on_progress)
            elif multilingual.enabled:
                coordinator = ExternalRequestCoordinator(
                    multilingual.max_external_calls_per_batch,
                    RatePacer(
                        config.max_requests,
                        config.window_seconds,
                        config.pacing_margin_seconds,
                    ),
                    on_pacing,
                )
                results, dropped, summary = analyze_dataframe_multilingual(
                    frame,
                    column,
                    get_predictor(),
                    LocalLanguageDetector(),
                    CerebrasTranslationProvider(api_key=_streamlit_cerebras_key(), max_retries=1),
                    multilingual,
                    config,
                    CerebrasSentimentReviewProvider(api_key=_streamlit_cerebras_key(), max_retries=1)
                    if config.enabled else None,
                    coordinator,
                    on_progress,
                )
            else:
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
            st.session_state["batch_summary"] = summary
            st.session_state["batch_summary_kind"] = (
                "direct" if direct_config.enabled else
                "legacy_multilingual" if multilingual.enabled else
                "hybrid"
            )
            st.session_state.pop("hybrid_summary", None)
            st.session_state.pop("ai_report", None)
            render_batch_summary_band(len(results), dropped)
            if direct_config.enabled:
                st.info(f"Llamadas externas consumidas: {summary['external_calls_used']:,} de {summary['external_call_limit']:,}; revisiones directas {summary['direct_reviews_attempted']:,}.")
            elif multilingual.enabled:
                st.info(
                    f"Llamadas externas consumidas: {summary['external_calls_used']:,} de "
                    f"{summary['external_call_limit']:,} (traducciones {summary['translations_attempted']:,}; "
                    f"second checks {summary['reviews_attempted']:,})."
                )
            elif summary["review_budget_exceeded"]:
                st.warning(f"{summary['review_budget_exceeded']:,} comentarios adicionales conservaron la clasificación local por límite de revisión IA.")
        except (CSVValidationError, ValueError) as exc:
            st.error(str(exc))
        except Exception:
            st.error("No fue posible completar el análisis masivo.")
    results = get_batch_results()
    if results is not None:
        render_batch_results_header()
        metrics = calculate_metrics(results)
        render_batch_kpi_cards(metrics)
        display = results.copy()
        if "review_state" in display:
            display["review_state"] = display["review_state"].map(REVIEW_STATE_LABELS).fillna("Estado desconocido")
        if "translation_state" in display:
            display["translation_state"] = display["translation_state"].map(TRANSLATION_STATE_LABELS).fillna("Estado desconocido")
        if "direct_review_state" in display:
            display["direct_review_state"] = display["direct_review_state"].map(DIRECT_REVIEW_STATE_LABELS).fillna("Estado desconocido")
        if "translation_error_code" in display:
            display["translation_error_code"] = display["translation_error_code"].map(
                lambda value: EXTERNAL_ERROR_LABELS.get(value, value)
            )
        percentage_columns = [name for name in display if name.startswith("probability_")]
        for name in ["confidence", "local_confidence"]:
            if name in display:
                display[name] = display[name].map(lambda value: f"{value:.1%}")
        for name in percentage_columns:
            display[name] = display[name].map(lambda value: f"{value:.1%}")
        display = display.rename(columns={"review_state": "Estado de revisión", "translation_state": "Estado de traducción", "direct_review_state": "Estado de revisión directa"})
        st.dataframe(display.head(100), width="stretch", hide_index=True)
        summary = st.session_state.get("batch_summary")
        summary_kind = st.session_state.get("batch_summary_kind")
        if isinstance(summary, dict) and isinstance(summary_kind, str):
            render_batch_traceability(results, summary, summary_kind)
        st.download_button(
            "Descargar CSV procesado",
            data=results.to_csv(index=False).encode("utf-8-sig"),
            file_name="sentiment_analysis_results.csv",
            mime="text/csv",
            width="stretch",
        )


def render_batch_traceability(results: pd.DataFrame, summary: dict, kind: str) -> None:
    if kind == "direct":
        states = results["direct_review_state"].value_counts()
        st.caption(
            f"Trazabilidad directa: Modelo local {int(states.get('local_only', 0)):,} · "
            f"Revisiones multilingües {int(states.get('direct_multilingual_review', 0)):,} · "
            f"Fallback local {summary['direct_review_fallbacks']:,} · "
            f"Llamadas externas {summary['external_calls_used']:,}/{summary['external_call_limit']:,}"
        )
        return
    if kind in {"hybrid", "legacy_multilingual"}:
        st.caption(
            f"Trazabilidad: Modelo local {summary['local_only']:,} · "
            f"Confirmados por second check {summary['reviewed']:,} · "
            f"Corregidos por second check {summary['disagreement']:,} · "
            f"Fallback local {summary['fallback']:,}"
        )
        return
    raise ValueError(f"Tipo de resumen batch no soportado: {kind}")


def render_dashboard() -> None:
    try:
        results, metrics, pareto = get_analysis()
    except ValueError as exc:
        render_workspace_empty_state(str(exc))
        return
    view = build_dashboard_view_model(metrics, pareto)
    render_dashboard_kpis(view)
    distribution = sentiment_distribution(metrics)
    left, right = st.columns([1.35, 0.85], gap="medium")
    with left:
        with st.container(border=True):
            render_panel_heading(
                "Panorama general",
                "Distribución de sentimientos",
                "Composición del lote según la clasificación final.",
            )
            render_sentiment_distribution_chart(distribution, int(metrics["total"]))
    with right:
        render_attention_panel(view)

    technical, reading = st.columns([1.35, 0.85], gap="medium")
    with technical:
        with st.container(border=True):
            render_panel_heading(
                "Contexto técnico",
                "Confianza local por clase",
                "Promedio de la probabilidad asignada por el modelo local.",
            )
            render_confidence_context_chart(results)
            st.caption("La confianza es una estimación interna del modelo local, no una garantía de corrección.")
    with reading:
        render_dataset_reading(view, build_traceability_text(results))


def render_pareto() -> None:
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
    figure.add_trace(go.Bar(x=pareto["topic"], y=pareto["frequency"], name="Frecuencia", marker_color="#4F46E5"), secondary_y=False)
    figure.add_trace(go.Scatter(x=pareto["topic"], y=pareto["cumulative_percentage"], name="% acumulado", mode="lines+markers", line=dict(color="#D92D20", width=3)), secondary_y=True)
    figure.add_hline(y=80, line_dash="dash", line_color="#667085", annotation_text="80%", secondary_y=True)
    figure.update_yaxes(title_text="Frecuencia", secondary_y=False)
    figure.update_yaxes(title_text="Porcentaje acumulado", range=[0, 105], ticksuffix="%", secondary_y=True)
    apply_plotly_theme(figure, height=520, top_margin=30, right_margin=0, showlegend=True)
    figure.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(figure, use_container_width=True)


def _streamlit_cerebras_key() -> str | None:
    try:
        return st.secrets.get("CEREBRAS_API_KEY") or os.getenv("CEREBRAS_API_KEY")
    except Exception:
        return os.getenv("CEREBRAS_API_KEY")


def render_report() -> None:
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
    multilingual_enabled = get_multilingual_config().enabled
    direct_enabled = get_direct_review_config().enabled
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
    if direct_enabled:
        st.write("La detección y el routing de textos largos se realizan localmente. Los textos EN/PT/IT detectados y los textos breves de idioma incierto pueden enviarse a Cerebras, proveedor externo, para revisión directa; se envía únicamente el comentario anonimizado, nunca otras columnas del CSV, y el original permanece en la aplicación. El informe IA agregado es una funcionalidad separada.")
    elif multilingual_enabled:
        st.write("La detección de idioma es local. Los comentarios que requieren traducción se anonimizan antes de enviarse a Cerebras; nunca se envían otras columnas del CSV y el texto original queda preservado en la app. Los second checks, si están habilitados por separado, comparten el mismo límite externo.")
    elif hybrid_enabled:
        st.write("La clasificación local ocurre primero. Sólo comentarios derivados pueden enviarse anonimizados a Cerebras para second check; nunca se envían otras columnas del CSV. El informe IA permanece separado y sólo recibe agregados.")
    else:
        st.write("La clasificación y el dashboard son locales. Cerebras sólo recibe métricas y frecuencias agregadas; las etiquetas textuales de los temas también se excluyen. Nunca se envían comentarios, el CSV ni sus otras columnas.")


load_global_styles()

with st.sidebar:
    render_sidebar_brand()
    page = st.radio(
        "Navegación",
        [
            "Análisis individual",
            "Análisis masivo",
            "Dashboard",
            "Pareto 80/20",
            "Informe ejecutivo",
            "Acerca del proyecto",
        ],
        label_visibility="collapsed",
        format_func=format_navigation_label,
    )
    batch_results = get_batch_results()
    render_dataset_context(len(batch_results) if batch_results is not None else None)
    render_sidebar_signature()

render_page_header(page)

pages = {
    "Análisis individual": render_individual_controlled,
    "Análisis masivo": render_batch_controlled,
    "Dashboard": render_dashboard,
    "Pareto 80/20": render_pareto,
    "Informe ejecutivo": render_report,
    "Acerca del proyecto": render_about,
}
pages[page]()
