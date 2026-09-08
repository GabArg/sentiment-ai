"""Presentation helpers for the project and privacy overview."""

from __future__ import annotations

import html

from .html import render_html


def build_privacy_copy(*, direct: bool, multilingual: bool, hybrid: bool) -> str:
    """Explain local, optional text review, and aggregate report data flows."""
    external_routes = []
    if direct:
        external_routes.append(
            "La revisión externa está habilitada: los textos EN/PT/IT detectados y los textos "
            "breves de idioma incierto pueden enviarse a Cerebras para revisión directa."
        )
    elif multilingual:
        external_routes.append(
            "La ruta multilingüe está habilitada: los comentarios que requieren traducción "
            "pueden enviarse a Cerebras y recibir después una revisión si esa opción está activa."
        )
    if hybrid:
        external_routes.append(
            "La revisión híbrida está habilitada: después de la clasificación local, los casos "
            "derivados por el router pueden enviarse a Cerebras para un second check."
        )
    if not external_routes:
        external_routes.append(
            "La revisión externa de comentarios está desactivada en la configuración actual. "
            "Si se habilita, sólo los casos previstos por la ruta configurada pueden enviarse."
        )
    external_review = " ".join(external_routes)
    return (
        "El análisis local clasifica comentarios y calcula métricas sin enviarlos a un proveedor "
        "externo. "
        f"{external_review} Antes de enviar texto para traducción o revisión, la aplicación "
        "aplica anonimización; la ruta envía el comentario anonimizado y excluye las demás "
        "columnas del CSV. El informe agregado es una "
        "acción opcional y separada: su contrato envía conteos, porcentajes y métricas resumidas, "
        "no comentarios individuales ni el archivo CSV. La anonimización reduce la exposición, "
        "pero nombres propios o contexto libre pueden permanecer y no existe una garantía de "
        "desidentificación completa."
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
            <h2>Una forma clara de revisar el feedback de clientes</h2>
            <p>Sentiment AI clasifica comentarios como positivos, neutros o negativos y organiza
            los resultados para facilitar su revisión, sin presentar las predicciones como certezas.</p></div>
            <aside><strong>Disponible actualmente</strong><span>Análisis individual y masivo,
            dashboard, Pareto léxico, informe y revisión externa opcional.</span></aside>
        </section>
        <section class="about-section">
            <span class="about-eyebrow">QUÉ PUEDE HACER</span><h3>Del comentario al informe</h3>
            <div class="about-pipeline">
                <article><b>01</b><strong>Analizar</strong><span>Un comentario o un archivo CSV validado</span></article>
                <i>→</i><article><b>02</b><strong>Clasificar</strong><span>Sentimiento y probabilidades del modelo local</span></article>
                <i>→</i><article><b>03</b><strong>Explorar</strong><span>Distribución, trazabilidad y términos frecuentes</span></article>
                <i>→</i><article><b>04</b><strong>Comunicar</strong><span>Informe determinístico y exportaciones</span></article>
            </div>
        </section>
        <section class="about-grid">
            <article><span class="about-card-icon">INFORMACIÓN</span><h3>Qué permite revisar</h3>
            <p>Distribución de sentimientos, probabilidades locales, términos frecuentes en
            comentarios negativos, trazabilidad de procesamiento y resultados descargables.</p></article>
            <article><span class="about-card-icon external">ALCANCE</span><h3>Qué no determina</h3>
            <p>No identifica causas reales, categorías de negocio ni tendencias temporales.
            El resultado del modelo requiere criterio humano, especialmente fuera de dominio.</p></article>
        </section>
        <section class="about-privacy"><div>DATOS</div><article><h3>Privacidad y tratamiento de datos</h3>
            <p>{privacy}</p></article></section>
        <section class="about-grid about-method">
            <article><span class="about-eyebrow">CÓMO SE PROCESA</span><h3>Modelo local y rutas opcionales</h3>
            <p>La base es un modelo ternario TF-IDF con regresión logística. Según la configuración,
            traducciones o revisiones externas pueden complementar el resultado con fallback observable.</p></article>
            <article><span class="about-eyebrow">METODOLOGÍA Y LÍMITES</span><h3>Una lectura, no una explicación causal</h3>
            <p>Pareto ordena n-gramas frecuentes y las métricas resumen clasificaciones disponibles.
            El modelo muestra debilidad conocida en neutrales factuales fuera del dominio histórico.</p></article>
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
