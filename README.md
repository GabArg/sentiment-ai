# Sentiment AI

Sentiment AI es un dashboard de customer feedback que combina clasificación local, análisis masivo, métricas de negocio y revisiones de IA opcionales. La aplicación funciona en modo local por defecto; los servicios externos sólo se activan mediante flags o acciones explícitas.

## Demo / qué resuelve

La aplicación transforma comentarios individuales o archivos CSV en información útil para explorar la experiencia del cliente:

- clasifica sentimientos con resultado y origen trazables;
- procesa hasta 10.000 filas conservando el orden y permite exportarlas en UTF-8;
- presenta distribución, confianza local y métricas de negocio;
- identifica temas negativos y construye un Pareto 80/20;
- genera un informe ejecutivo determinístico y, opcionalmente, una redacción asistida por IA.

## Origen del proyecto

Sentiment AI nació como **H12-25-L-Equipo-72**, un proyecto colaborativo de No Country. Los integrantes que participaron activamente en el proyecto fueron:

- Carlos Mauricio Rondón
- Juan Carlos Vanegas Molina
- Guido Arturo Broccoli
- Neldy Rolando Velásquez Samolo
- José Julián Gómez Brizuela

El modelo original, sus artefactos y las primeras implementaciones surgieron del trabajo grupal. El proyecto histórico incluyó una arquitectura con FastAPI/OCI, frontend web, análisis de sentimiento y capacidades documentadas de traducción y revisión con Cerebras. No se presenta ese trabajo como creación exclusiva de una sola persona.

La procedencia técnica, los repositorios históricos y el alcance de las contribuciones están documentados en [ATTRIBUTION.md](ATTRIBUTION.md).

## Evolución para portfolio

A partir de esa base histórica, retomé el proyecto, recuperé una versión reproducible del modelo y desarrollé una evolución técnica orientada a portfolio, analítica de negocio, confiabilidad y uso responsable de IA.

Esta evolución posterior incorporó:

- recuperación reproducible de los artefactos TF-IDF + LogisticRegression;
- inferencia local y arquitectura modular;
- análisis individual y procesamiento batch de archivos CSV;
- dashboard de analytics y métricas de negocio;
- extracción de temas negativos y Pareto 80/20;
- informe ejecutivo determinístico y redacción IA opcional;
- revisión híbrida opt-in para casos derivados por un router auditable;
- evaluación del modelo local y benchmark manual versionado;
- arquitectura multilingüe experimental;
- direct structured review para ES/EN/PT/IT mediante Structured Outputs y JSON Schema;
- anonimización, minimización de datos y fallback observable;
- límites de presupuesto, control de rate limits y pacing compartido;
- tests automatizados, GitHub Actions CI y documentación técnica;
- preparación y publicación de la release candidate `v2.0.0-rc1`.

El soporte multilingüe sigue siendo experimental: fue validado sobre muestras pequeñas y curadas, no como una capacidad productiva general.

## Resultados y validación

| Evaluación | Resultado | Alcance |
|---|---:|---|
| holdout histórico reconstruido | ~89.42% | corpus histórico; no reentrenado en v2 |
| baseline local manual | 31/60, 51.67% | benchmark dirigido externo; neutral débil |
| hybrid manual | 59/60, 98.33% | mismo benchmark pequeño; Cerebras sólo en derivados |
| multilingüe directo | 47/48, 97.92% | muestra curada ES/EN/PT/IT; no benchmark general |
| pacing endurecido | 15/15 success, 0 HTTP 429 | prueba operativa separada; no mide accuracy |

Estas métricas corresponden a evaluaciones distintas, no son intercambiables y no representan rendimiento productivo. Los experimentos completos están indexados en [docs/experiments/README.md](docs/experiments/README.md).

## Arquitectura

```text
texto / CSV → validación
├─ español largo → TF-IDF + LogisticRegression → hybrid opcional
├─ EN/PT/IT largo → direct structured review opcional
├─ <=4 tokens → short_text_uncertain → direct review opcional
└─ errores externos → fallback local observable

resultados → dashboard → temas/Pareto → informe → exports
```

La ruta recomendada para textos no españoles es una sola llamada estructurada sobre el comentario anonimizado. La traducción previa a español permanece disponible como ruta legacy/experimental por fidelidad histórica. Más detalles: [arquitectura](docs/architecture.md) y [ADR 001](docs/adr/001-direct-multilingual-review.md).

## Privacidad

Los flags están OFF por defecto. Cuando hay revisión o traducción externa se envía sólo el comentario anonimizado, sin expected, confianza local, fila completa ni columnas de negocio. El informe IA recibe únicamente agregados minimizados. La anonimización reduce el riesgo, pero no garantiza la desidentificación de nombres o contexto libre. Véase [docs/privacy.md](docs/privacy.md).

## Calidad de ingeniería

- 214 tests automatizados;
- 90% de cobertura sobre `src`;
- GitHub Actions CI para pull requests y `main`;
- validaciones con `compileall` y `pip check`;
- fallbacks explícitos ante errores externos;
- separación entre inferencia local y servicios externos;
- flags externos OFF por defecto;
- trazabilidad de rutas, budgets y estados de revisión.

## Instalación

Requiere Python 3.12.

```bash
git clone https://github.com/GabArg/sentiment-ai.git
cd sentiment-ai
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Configuración

Copiá `.streamlit/secrets.toml.example` como `.streamlit/secrets.toml` o usá variables de entorno. Nunca versiones el archivo real.

```toml
CEREBRAS_API_KEY = "..."

ENABLE_HYBRID_SENTIMENT = false
ENABLE_MULTILINGUAL_SENTIMENT = false       # traducción legacy
ENABLE_DIRECT_MULTILINGUAL_REVIEW = false   # ruta moderna candidata

HYBRID_THRESHOLD_NEGATIVE = 0.80
HYBRID_THRESHOLD_NEUTRAL = 0.65
HYBRID_THRESHOLD_POSITIVE = 0.80
HYBRID_MAX_EXTERNAL_CALLS_PER_BATCH = 25
HYBRID_MAX_REQUESTS = 5
HYBRID_WINDOW_SECONDS = 60
EXTERNAL_RATE_LIMIT_SAFETY_SECONDS = 2.0
```

Configurar la API key no activa ningún modo. El informe IA se genera sólo al pulsar su botón. La tabla completa de precedencia y aliases está en [docs/architecture.md](docs/architecture.md).

## Testing

```bash
pip install -r requirements-dev.txt
pytest --cov=src --cov-report=term-missing
python -m compileall app.py src scripts tests
python -m pip check
```

## Limitaciones

- El modelo local fue entrenado históricamente y falla especialmente en neutrales fuera de dominio.
- El benchmark multilingüe es pequeño, manual y limitado a ES/EN/PT/IT.
- Los textos breves no usan detección de idioma; se marcan como inciertos.
- Los modos externos dependen de disponibilidad, cuota, costo y límites de Cerebras.
- El Free Tier configurado para la demo usa pacing conservador y puede hacer lento un batch.
- Los temas negativos son señales léxicas, no causas de negocio inferidas.

## Historia y créditos

Sentiment AI tiene dos etapas claramente diferenciadas: el proyecto grupal original de No Country y la recuperación/evolución v2 desarrollada posteriormente en este repositorio. La autoría de ambas etapas se documenta por separado para preservar correctamente la procedencia del trabajo.

Los créditos completos, las fuentes históricas y el detalle de la evolución están en [ATTRIBUTION.md](ATTRIBUTION.md). El proyecto se distribuye bajo [GPL-3.0](LICENSE).
