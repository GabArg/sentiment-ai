# Sentiment AI v2

Aplicación de **Customer Feedback Analytics** que combina NLP clásico, análisis masivo y reporting ejecutivo. Clasifica comentarios con TF-IDF y regresión logística, resume métricas de negocio, extrae temas negativos, calcula un Pareto 80/20 y genera un informe reproducible. Como mejora opcional, Cerebras puede redactar una segunda versión ejecutiva a partir de datos agregados y minimizados.

> Este repositorio conserva tres capas claramente diferenciadas: el proyecto grupal original de No Country, su recuperación técnica V6 para portfolio y esta evolución v2 posterior. El software original no se presenta como trabajo individual. Véase [ATTRIBUTION.md](ATTRIBUTION.md).

## Capacidades

- análisis individual con etiqueta, confianza y distribución por clase;
- carga CSV con detección de columnas, previsualización, nulos y límites de seguridad;
- inferencia vectorizada de hasta 10.000 filas;
- dashboard de distribución, confianza y visión de negocio;
- extracción determinística de temas negativos mediante frecuencia documental de unigramas y bigramas;
- Pareto 80/20 con tabla, barras y porcentaje acumulado;
- informe ejecutivo determinístico, disponible siempre;
- informe IA opcional con Cerebras, sólo por acción explícita;
- exportación del CSV procesado y del informe en Markdown.

La aplicación no requiere FastAPI, localhost, datasets, descargas de modelos ni servicios externos para sus funciones principales.

## Arquitectura

```text
Usuario -> Streamlit -> texto / CSV -> validación
        -> TF-IDF -> Logistic Regression -> clase + probabilidades
        -> agregaciones -> dashboard -> temas -> Pareto
        -> informe determinístico
        -> Cerebras opcional (contexto agregado y anonimizado)
```

Los artefactos originales se cargan una vez con `st.cache_resource`. `model.classes_` define en runtime la asociación entre clases y probabilidades; no se presupone su orden.

## Modelo y NLP

- vectorizador: `TfidfVectorizer`, unigramas y bigramas, hasta 5.000 features;
- clasificador: `LogisticRegression` multiclase, `class_weight="balanced"`, solver `newton-cg`;
- clases serializadas: `Negativo`, `Neutro`, `Positivo`;
- serialización: joblib y scikit-learn 1.8.0;
- datos históricos: `dataset_unificado.csv`, construido por el equipo a partir de tres CSV, incluido un conjunto sintético multilingüe V6.

La v2 no reentrena el modelo. Incluye un benchmark externo/manual reproducible de 60 frases para medir regresiones y casos fuera del dominio original. El holdout reconstruido del corpus alcanza aproximadamente 89,42 % de accuracy; sobre el benchmark manual el baseline actual es 51,67 % global y 20 % para Neutro. La segunda cifra describe únicamente ese benchmark pequeño y dirigido, no el rendimiento general del modelo.

La confianza es la probabilidad interna asignada por el clasificador, no una garantía de acierto. Existen errores con confianza igual o superior a 80 %, por lo que ese valor no debe interpretarse como certeza ni como regla suficiente para una futura arquitectura híbrida. La metodología, observabilidad y discrepancia de preprocessing están documentadas en [docs/quality-evaluation.md](docs/quality-evaluation.md).

La arquitectura híbrida está disponible como preview experimental y **opt-in**. Permanece desactivada por defecto, por lo que la UI y los resultados siguen siendo locales salvo configuración explícita. Cuando se habilita, usa routing por clase, second check estructurado, fallback local, budget y pacing. La variante Fase 2.3 alcanzó 98,33% con 50 revisiones en el benchmark manual versionado de 60 casos; no representa accuracy productiva. Véase [docs/hybrid-classification.md](docs/hybrid-classification.md).

El modo multilenguaje experimental también es **opt-in** e independiente. Detecta localmente español, inglés, portugués e italiano y puede traducir a español mediante Cerebras `gpt-oss-120b`; preserva el original y sólo envía el comentario anonimizado, nunca otras columnas. El detector obtuvo 95,83% en 48 frases, pero fue menos fiable en español corto (83,33%). Una validación real limitada a seis traducciones preservó la semántica, aunque traducción→modelo local no mejoró la accuracy en esa muestra. No representa calidad productiva. Véanse [la arquitectura](docs/multilingual-architecture.md) y [la validación](docs/multilingual-validation.md).

### Prueba multilingüe exploratoria

| Idioma | Positivo | Negativo | Neutro |
|---|---|---|---|
| Español | Positivo (98,4 %) | Negativo (77,3 %) | Neutro (59,0 %) |
| Inglés | Positivo (66,5 %) | Negativo (74,6 %) | Neutro (47,8 %) |
| Portugués | Positivo (89,8 %) | **Neutro (52,7 %)** | Neutro (64,0 %) |

Son nueve pruebas manuales, no una evaluación estadística. El fallo del ejemplo negativo en portugués indica que no debe afirmarse soporte multilingüe robusto sin un conjunto de evaluación etiquetado. No se añadió traducción automática.

## Batch, temas y Pareto

El CSV puede usar coma, punto y coma, tabulación o barra vertical. La persona elige la columna de texto; las filas nulas, vacías o demasiado cortas se excluyen. El límite es 10 MB y 10.000 registros para proteger los recursos de Streamlit Community Cloud.

Para los comentarios clasificados como negativos, `CountVectorizer` normaliza acentos, elimina stopwords en español, inglés y portugués y calcula frecuencia por documento. Se priorizan bigramas y se eliminan unigramas redundantes. Estos términos son **señales léxicas**, no categorías ni causas inferidas. El Pareto ordena menciones por frecuencia y marca el conjunto mínimo que alcanza el 80 % acumulado.

La nube de palabras se omitió: agrega una dependencia y suele comunicar peor que la tabla y el Pareto cuantificado.

## Informes y Cerebras

El informe determinístico contiene distribución, principales problemas, Pareto, oportunidades y limitaciones calculadas. Funciona sin credenciales.

La opción IA usa el SDK oficial `cerebras_cloud_sdk` y el modelo `gpt-oss-120b`. La [documentación oficial](https://inference-docs.cerebras.ai/models/openai-oss) lo recomienda para resumen; el [catálogo](https://inference-docs.cerebras.ai/models/overview) publica aproximadamente 3.000 tokens/s y precios de USD 0,35 por millón de tokens de entrada y USD 0,75 por millón de salida. Los precios y modelos pueden cambiar.

La llamada ocurre únicamente al pulsar **Generar informe con IA**. Se envían conteos, porcentajes, confianza media y frecuencias agregadas del Pareto. Las etiquetas textuales de los temas se mantienen locales porque podrían contener información identificable. Nunca se envían comentarios, el CSV completo ni sus otras columnas. Si falta la clave, hay timeout, cuota, error o respuesta inválida, se conserva el informe determinístico.

## Estructura

```text
app.py                         interfaz y navegación Streamlit
src/model.py                   carga e inferencia local
src/preprocessing.py           CSV, validación y anonimización
src/batch.py                   análisis vectorizado
src/analytics.py               métricas de negocio
src/pareto.py                  temas y cálculo 80/20
src/reporting.py               prompt e informe determinístico
src/ai_provider.py             integración opcional y fallback
src/review_router.py           reglas experimentales de incertidumbre
src/sentiment_review.py        contrato y adaptador de second check
src/hybrid.py                  consolidación local/híbrida estructurada y reversible
src/hybrid_config.py           feature flag, thresholds, budget y costo orientativo
src/rate_pacer.py              pacing secuencial inyectable para batch
src/language_detection.py      detector local determinístico
src/translation.py             provider estructurado de traducción
src/multilingual_pipeline.py   preparación y clasificación multilenguaje
src/external_requests.py       pacing y budget compartidos
src/router_evaluation.py       evaluación offline de estrategias
models/                        artefactos joblib originales
tests/                         pruebas unitarias y funcionales
tests/fixtures/                benchmark manual de evaluación, nunca de entrenamiento
docs/quality-evaluation.md     baseline, observabilidad y preprocessing
docs/hybrid-classification.md  arquitectura híbrida, privacidad y fallback
.streamlit/secrets.toml.example
```

## Instalación y ejecución

Requiere Python 3.12.

```bash
git clone https://github.com/GabArg/sentiment-ai.git
cd sentiment-ai
git switch feature/v2-dashboard-ai-report
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Pruebas:

```bash
pip install -r requirements-dev.txt
pytest --cov=src --cov-report=term-missing
python -m compileall app.py src tests
python -m src.evaluation
python -m src.router_evaluation
```

## Configuración opcional de Cerebras

Usá una variable de entorno `CEREBRAS_API_KEY` o copiá `.streamlit/secrets.toml.example` como `.streamlit/secrets.toml` y completala localmente. El archivo real está ignorado y nunca debe versionarse.

En Streamlit Community Cloud:

```text
Repository: GabArg/sentiment-ai
Branch: feature/v2-dashboard-ai-report
Main file: app.py
Advanced settings > Secrets: CEREBRAS_API_KEY = "..."  # opcional
```

Sin secret, toda la aplicación salvo la redacción IA continúa operativa.

Para habilitar manualmente el preview híbrido:

```toml
ENABLE_HYBRID_SENTIMENT = true
CEREBRAS_API_KEY = "..."
HYBRID_THRESHOLD_NEGATIVE = 0.80
HYBRID_THRESHOLD_NEUTRAL = 0.65
HYBRID_THRESHOLD_POSITIVE = 0.80
HYBRID_MAX_REVIEWS_PER_BATCH = 25
```

No habilites el flag únicamente por configurar la API key: son opciones independientes. Los thresholds son experimentales y reversibles; desactivar el flag restaura el comportamiento local sin cambiar artefactos.

Para habilitar manualmente el preview multilenguaje:

```toml
ENABLE_MULTILINGUAL_SENTIMENT = true
CEREBRAS_API_KEY = "..."
HYBRID_MAX_EXTERNAL_CALLS_PER_BATCH = 25
```

La ruta moderna de revisión multilingüe directa es experimental y opt-in:

```toml
ENABLE_DIRECT_MULTILINGUAL_REVIEW = true
```

Con esta opción, textos EN/PT/IT de más de cuatro tokens y textos breves de idioma
incierto se revisan directamente con un contrato JSON estricto, sin traducción previa.
El default permanece `false` y no constituye soporte productivo universal.

La detección puede ser menos fiable en textos breves o ambiguos. Habilitar multilenguaje no activa automáticamente el second check híbrido.

## Evolución y atribución

1. **Proyecto original:** desarrollo grupal H12-25-L-Equipo-72 dentro de No Country.
2. **Recuperación V6:** adaptación del clasificador TF-IDF + Logistic Regression como demo independiente de portfolio.
3. **Evolución v2:** nueva implementación modular de batch, dashboard, temas, Pareto, informes, privacidad, Cerebras opcional, exportación y tests en este repositorio.

Los nombres del equipo y el alcance verificable de la participación de Guido están documentados sin inferir roles en [ATTRIBUTION.md](ATTRIBUTION.md).

## Licencia

Este trabajo derivado se distribuye bajo [GNU GPL v3.0](LICENSE), como el proyecto original. Deben conservarse la licencia, la procedencia y los avisos de modificación.
