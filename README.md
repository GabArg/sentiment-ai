# Sentiment AI

**Análisis de Opiniones de Clientes**

Sentiment AI es una aplicación de portfolio para clasificar, explorar y comunicar feedback de clientes. Funciona con un modelo local por defecto y mantiene separadas las revisiones externas opcionales, con trazabilidad sobre el origen de cada resultado.

[Abrir la demo](https://sentiment-ai-fu52eqobppy4baddnslh6c.streamlit.app)

**Stack:** Python · Streamlit · scikit-learn · Pandas · Plotly · Cerebras (opcional)

## Qué permite hacer

- Analizar un comentario y consultar las probabilidades del modelo local.
- Procesar archivos CSV de hasta 10.000 filas, conservar su orden y exportar resultados en UTF-8.
- Revisar distribución de sentimientos, confianza local y trazabilidad de las rutas utilizadas.
- Ordenar n-gramas frecuentes del feedback negativo mediante un Pareto 80/20.
- Generar un informe ejecutivo determinístico y descargarlo.
- Solicitar, cuando está configurado, revisión externa o redacción asistida sobre datos minimizados.

El Pareto es léxico: muestra términos frecuentes, no categorías semánticas, causas verificadas ni severidad de negocio.

## Cómo funciona

```text
texto / CSV → validación
├─ español largo → TF-IDF + LogisticRegression → revisión híbrida opcional
├─ EN/PT/IT largo → revisión multilingüe directa opcional
├─ texto breve → idioma incierto → revisión directa opcional
└─ error externo → fallback local observable

resultados → dashboard → términos/Pareto → informe → exportación
```

El clasificador local ternario usa un vectorizador TF-IDF y una regresión logística congelados. `confidence` es la probabilidad asignada por `predict_proba` a la clase elegida; sirve como contexto técnico, no como garantía calibrada de acierto.

Los modos externos están desactivados por defecto. Cuando una ruta habilitada envía texto, transmite únicamente el comentario anonimizado y no las otras columnas del CSV. El informe asistido recibe agregados minimizados. La anonimización reduce el riesgo, pero no garantiza desidentificación completa. Véase [Privacidad](docs/privacy.md).

## Vistas de la aplicación

- **Análisis individual:** resultado, probabilidades locales y trazabilidad progresiva.
- **Análisis masivo:** importación, configuración, vista previa, resultados y descarga.
- **Dashboard:** volumen, distribución, confianza local y términos negativos frecuentes.
- **Pareto 80/20:** concentración léxica del feedback clasificado como negativo.
- **Informe ejecutivo:** brief determinístico; la variante asistida por IA es independiente y opcional.
- **Acerca del proyecto:** arquitectura, metodología, privacidad, límites e historia.

## Ejecución local

Requiere Python 3.12.

```bash
git clone https://github.com/GabArg/sentiment-ai.git
cd sentiment-ai
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

No se necesita una cuenta de Cerebras para usar el análisis local, el procesamiento masivo, el dashboard, el Pareto ni el informe determinístico.

## Configuración externa opcional

Copiá `.streamlit/secrets.toml.example` como `.streamlit/secrets.toml` o usá variables de entorno. No versiones el archivo real ni muestres la API key en logs o capturas.

```toml
CEREBRAS_API_KEY = "..."

ENABLE_HYBRID_SENTIMENT = false
ENABLE_MULTILINGUAL_SENTIMENT = false
ENABLE_DIRECT_MULTILINGUAL_REVIEW = false

HYBRID_THRESHOLD_NEGATIVE = 0.80
HYBRID_THRESHOLD_NEUTRAL = 0.65
HYBRID_THRESHOLD_POSITIVE = 0.80
HYBRID_MAX_EXTERNAL_CALLS_PER_BATCH = 25
HYBRID_MAX_REQUESTS = 5
HYBRID_WINDOW_SECONDS = 60
EXTERNAL_RATE_LIMIT_SAFETY_SECONDS = 2.0
```

Configurar la clave no activa por sí solo ninguna ruta. El informe asistido se solicita mediante una acción explícita. La precedencia completa de configuración está documentada en [Arquitectura](docs/architecture.md).

## Evaluación y reproducibilidad

Las evaluaciones disponibles responden a condiciones distintas y no deben combinarse ni interpretarse como una garantía de rendimiento:

| Evaluación | Resultado observado | Condición principal |
|---|---:|---|
| Holdout histórico reconstruido | ~89,42% accuracy | split por filas del corpus histórico; comparte familias textuales y puede ser optimista |
| Benchmark manual de 60 | 51,67% accuracy; 20% recall neutro | muestra pequeña y dirigida, ya utilizada para diagnóstico |
| Demo sintético de 104 | 75,00% accuracy; 6,67% recall neutro | datos sintéticos, desbalanceados y no independientes |
| Revisión híbrida sobre los 60 | 98,33% accuracy | reproducción exploratoria sobre el mismo benchmark, con resultados externos observados |
| Validación multilingüe directa | 47/48 casos | muestra pequeña y curada ES/EN/PT/IT |

La principal debilidad observada es la neutralidad factual fuera del dominio histórico. Los 60 y 104 casos son benchmarks diagnósticos/regresivos, no conjuntos independientes para seleccionar modelos, reglas o thresholds. La [síntesis de evaluación](docs/quality-evaluation.md) explica matrices, condiciones y limitaciones; los reportes reproducibles completos permanecen en [artifacts/experiments](artifacts/experiments/).

Para ejecutar las comprobaciones locales:

```bash
python -m pip install -r requirements-dev.txt
pytest
python -m compileall app.py src scripts tests
python -m pip check
```

## Limitaciones conocidas

- El modelo local fue entrenado con un corpus histórico y generaliza peor a neutrales factuales y redacciones fuera de dominio.
- La confianza local no equivale a probabilidad calibrada de corrección.
- El Pareto cuenta n-gramas; no detecta categorías de negocio ni causalidad.
- Las validaciones híbrida y multilingüe son pequeñas y exploratorias.
- Los modos externos dependen de disponibilidad, cuota, costo y límites del proveedor.
- Los textos muy breves se marcan con idioma incierto en lugar de asumirlo.

## Alcance actual y trabajo futuro

Está implementada la experiencia local completa, junto con rutas externas opt-in, controles de privacidad, presupuestos, rate limiting, fallbacks, tests y documentación técnica. La investigación de neutralidad y el protocolo de anotación están versionados como trabajo experimental.

No están implementados un clasificador de categorías de negocio, un Pareto semántico ni una mejora de modelo seleccionada con evaluación humana independiente. Esos puntos permanecen como trabajo futuro.

## Historia y atribución

Sentiment AI nació como **H12-25-L-Equipo-72**, un proyecto colaborativo de No Country. Carlos Mauricio Rondón, Juan Carlos Vanegas Molina, Guido Arturo Broccoli, Neldy Rolando Velásquez Samolo y José Julián Gómez Brizuela participaron activamente en esa etapa. El modelo original, sus artefactos y las primeras implementaciones surgieron de ese trabajo grupal.

Posteriormente retomé el proyecto para recuperar una versión reproducible y desarrollar esta evolución de portfolio. La procedencia técnica, los repositorios históricos y el alcance de cada etapa están documentados en [ATTRIBUTION.md](ATTRIBUTION.md); no se presenta el trabajo grupal como creación exclusiva de una sola persona.

El proyecto se distribuye bajo [GPL-3.0](LICENSE).
