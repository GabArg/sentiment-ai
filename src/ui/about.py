"""Presentation helpers for the project and privacy overview."""

from __future__ import annotations

import html

from .html import render_html


def build_privacy_copy(*, direct: bool, multilingual: bool, hybrid: bool) -> str:
    """Return the established privacy disclosure for the active routing mode."""
    if direct:
        return (
            "La detección y el routing de textos largos se realizan localmente. Los textos "
            "EN/PT/IT detectados y los textos breves de idioma incierto pueden enviarse a "
            "Cerebras, proveedor externo, para revisión directa; se envía únicamente el "
            "comentario anonimizado, nunca otras columnas del CSV, y el original permanece "
            "en la aplicación. El informe IA agregado es una funcionalidad separada."
        )
    if multilingual:
        return (
            "La detección de idioma es local. Los comentarios que requieren traducción se "
            "anonimizan antes de enviarse a Cerebras; nunca se envían otras columnas del CSV "
            "y el texto original queda preservado en la app. Los second checks, si están "
            "habilitados por separado, comparten el mismo límite externo."
        )
    if hybrid:
        return (
            "La clasificación local ocurre primero. Sólo comentarios derivados pueden "
            "enviarse anonimizados a Cerebras para second check; nunca se envían otras columnas "
            "del CSV. El informe IA permanece separado y sólo recibe agregados."
        )
    return (
        "La clasificación y el dashboard son locales. Cerebras sólo recibe métricas y "
        "frecuencias agregadas; las etiquetas textuales de los temas también se excluyen. "
        "Nunca se envían comentarios, el CSV ni sus otras columnas."
    )


def render_about_overview(*, direct: bool, multilingual: bool, hybrid: bool) -> None:
    """Render the product story without changing operational configuration."""
    privacy = html.escape(
        build_privacy_copy(direct=direct, multilingual=multilingual, hybrid=hybrid)
    )
    render_html(
        f"""
        <section class="about-hero">
            <div><span class="about-eyebrow">ANÁLISIS DE OPINIONES DE CLIENTES</span>
            <h2>Del comentario individual a una visión ordenada del feedback</h2>
            <p>Sentiment AI organiza comentarios, muestra la distribución de sentimiento
            y permite revisar términos frecuentes, con trazabilidad sobre cada ruta.</p></div>
            <aside><strong>Información para revisar</strong><span>Clasificación reproducible,
            analítica agregada y revisión externa opcional.</span></aside>
        </section>
        <section class="about-section">
            <span class="about-eyebrow">CÓMO FUNCIONA</span><h3>Pipeline de procesamiento</h3>
            <div class="about-pipeline">
                <article><b>01</b><strong>Ingreso</strong><span>Texto individual o CSV validado</span></article>
                <i>→</i><article><b>02</b><strong>Protección</strong><span>Detección y anonimización según ruta</span></article>
                <i>→</i><article><b>03</b><strong>Clasificación</strong><span>TF-IDF + regresión logística local</span></article>
                <i>→</i><article><b>04</b><strong>Lectura</strong><span>Dashboard, Pareto e informe</span></article>
            </div>
        </section>
        <section class="about-grid">
            <article><span class="about-card-icon">LOCAL</span><h3>Modelo reproducible</h3>
            <p>El modelo ternario local conserva sus artefactos, probabilidades y thresholds.
            Es la base de la experiencia analítica.</p></article>
            <article><span class="about-card-icon external">OPCIONAL</span><h3>Revisión externa</h3>
            <p>Las rutas configuradas pueden traducir o revisar casos controlados. Disponibilidad,
            cuota y límites externos siguen siendo restricciones explícitas.</p></article>
        </section>
        <section class="about-privacy"><div>PRIVACIDAD</div><article><h3>El dato sensible conserva su contexto</h3>
            <p>{privacy}</p></article></section>
        <section class="about-grid about-method">
            <article><span class="about-eyebrow">METODOLOGÍA Y LÍMITES</span><h3>Qué muestran las vistas</h3>
            <p>Las métricas resumen las clasificaciones disponibles. Pareto ordena n-gramas
            frecuentes: no los convierte en categorías semánticas ni afirma causalidad.</p></article>
            <article><span class="about-eyebrow">PROCEDENCIA</span><h3>Dos etapas, atribución separada</h3>
            <p>El proyecto original fue un desarrollo grupal de H12-25-L-Equipo-72 de No Country.
            La recuperación técnica y evolución posterior para portfolio se documentan por separado.</p></article>
        </section>
        <section class="about-team">
            <span class="about-eyebrow">ORIGEN Y EQUIPO</span>
            <h3>H12-25-L-Equipo-72 · No Country</h3>
            <p>Sentiment AI nació como un desarrollo colaborativo. Los integrantes cuya
            participación activa está confirmada son:</p>
            <div class="about-team-members">
                <span>Carlos Mauricio Rondón</span>
                <span>Juan Carlos Vanegas Molina</span>
                <span>Guido Arturo Broccoli</span>
                <span>Neldy Rolando Velásquez Samolo</span>
                <span>José Julián Gómez Brizuela</span>
            </div>
            <p class="about-team-note">El código, el entrenamiento, los datos preparados,
            los artefactos y las primeras implementaciones fueron resultado del trabajo grupal.
            No se asignan roles técnicos individuales sin evidencia verificable.</p>
            <div class="about-stages">
                <article><b>Proyecto original</b><span>Base colaborativa, modelo y primeras implementaciones.</span></article>
                <article><b>Recuperación técnica</b><span>Artefactos reproducibles e inferencia local para portfolio.</span></article>
                <article><b>Evolución posterior</b><span>Analytics, experiencia de producto, evaluación y documentación.</span></article>
            </div>
        </section>
        <section class="about-history"><strong>Historia verificable</strong><p>La aplicación actual se inspira
        funcionalmente en la aplicación histórica posterior, cuyo código no está disponible;
        no afirma reconstruir ese código. La atribución completa y las contribuciones verificables
        están en <code>ATTRIBUTION.md</code>.</p></section>
        """
    )
