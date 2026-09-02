# Sentiment AI

Dashboard de customer feedback que combina clasificación local, análisis masivo, métricas de negocio y revisiones IA opcionales. La aplicación funciona local-only por defecto; Cerebras se activa únicamente mediante flags o acciones explícitas.

> Evolución moderna del proyecto grupal H12-25-L-Equipo-72. La procedencia y las contribuciones verificables están separadas en [ATTRIBUTION.md](ATTRIBUTION.md).

## Funcionalidades

- análisis individual con resultado, evidencia local y origen trazable;
- CSV de hasta 10.000 filas, preservación de orden y export UTF-8;
- dashboard de distribución, confianza, temas negativos y Pareto 80/20;
- informe ejecutivo determinístico y segunda redacción IA opcional;
- hybrid second check configurable con fallback local;
- review multilingüe directo experimental para ES/EN/PT/IT;
- anonimización, budget global y rolling-window pacing compartido.

## Arquitectura

```text
texto / CSV → validación
├─ español largo → TF-IDF + LogisticRegression → hybrid opcional
├─ EN/PT/IT largo → direct structured review opcional
├─ <=4 tokens → short_text_uncertain → direct review opcional
└─ errores externos → fallback local observable

resultados → dashboard → temas/Pareto → informe → exports
```

La ruta recomendada para no-español es una sola llamada estructurada sobre el comentario anonimizado. La traducción previa a español permanece disponible como ruta legacy/experimental por fidelidad histórica. Detalle: [arquitectura](docs/architecture.md), [ADR 001](docs/adr/001-direct-multilingual-review.md).

## Privacidad

Los flags están OFF por defecto. Cuando hay revisión o traducción externa se envía sólo el comentario anonimizado, sin expected, confianza local, fila completa ni columnas de negocio. El informe IA recibe únicamente agregados minimizados. La anonimización reduce riesgo pero no garantiza desidentificación de nombres o contexto libre. Véase [docs/privacy.md](docs/privacy.md).

## Validación

| Evaluación | Resultado | Alcance |
|---|---:|---|
| holdout histórico reconstruido | ~89.42% | corpus histórico; no reentrenado en v2 |
| baseline local manual | 31/60, 51.67% | benchmark dirigido externo; neutral débil |
| hybrid manual | 59/60, 98.33% | mismo benchmark pequeño; Cerebras sólo en derivados |
| multilingüe directo | 47/48, 97.92% | muestra curada ES/EN/PT/IT; no benchmark general |
| pacing endurecido | 15/15 success, 0 HTTP 429 | prueba operativa separada; no mide accuracy |

Estas métricas no son intercambiables ni representan producción. Los experimentos completos están indexados en [docs/experiments/README.md](docs/experiments/README.md).

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

Configurar la API key no activa ningún modo. El informe IA se genera sólo al pulsar su botón. Tabla completa de precedencia y aliases: [docs/architecture.md](docs/architecture.md).

## Testing

```bash
pip install -r requirements-dev.txt
pytest --cov=src --cov-report=term-missing
python -m compileall app.py src scripts tests
python -m pip check
```

La release candidate mantiene cobertura `src` ≥90% y AppTests de los flujos local, hybrid, traducción legacy, direct, batch, dashboard e informes.

## Limitaciones

- El modelo local fue entrenado históricamente y falla especialmente en neutrales fuera de dominio.
- El benchmark multilingüe es pequeño, manual y limitado a ES/EN/PT/IT.
- Textos breves no usan detección de idioma; se marcan inciertos.
- Los modos externos dependen de disponibilidad, cuota, costo y límites de Cerebras.
- El Free Tier configurado para la demo usa pacing conservador y puede hacer lento un batch.
- Los temas negativos son señales léxicas, no causas de negocio inferidas.

## Historia y créditos

1. Proyecto grupal original H12-25-L-Equipo-72: FastAPI/OCI, frontend PHP/JavaScript/ChartJS, modelo y flujo histórico con Llama 3/Cerebras.
2. Recuperación V6: adaptación de artefactos TF-IDF + LogisticRegression a una demo independiente.
3. v2: dashboard modular, analytics, hybrid estructurado, multilenguaje directo, privacidad, observabilidad y suite de tests.

No se atribuye a Guido código histórico sin evidencia. Véanse [ATTRIBUTION.md](ATTRIBUTION.md) y [LICENSE](LICENSE) (GPL-3.0).
