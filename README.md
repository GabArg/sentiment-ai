# Sentiment AI

Aplicación web de análisis de sentimientos construida con Streamlit y Machine Learning clásico. Recibe una opinión escrita, la representa con TF-IDF y utiliza una regresión logística multiclase para devolver el sentimiento predicho y su probabilidad estimada.

> Esta es una versión **recuperada, modificada, simplificada y preparada para portfolio** del proyecto grupal [H12-25-L-Equipo-72](https://github.com/S4mma3l/H12-25-L-Equipo-72/tree/feature/mejora-dataset-v6). No se presenta el trabajo original del equipo como una creación individual. La procedencia y las modificaciones están detalladas en [ATTRIBUTION.md](ATTRIBUTION.md).

## Demo online

La URL pública se agregará aquí después de crear la aplicación en Streamlit Community Cloud.

## Problema

Equipos que reciben muchas reseñas o comentarios necesitan una primera clasificación que les permita organizar feedback positivo, negativo y neutro. La revisión manual no escala bien y dificulta una lectura inicial consistente.

## Solución

Esta demo ofrece una interfaz responsive donde una persona puede ingresar texto libre y obtener:

- la clase de sentimiento elegida por el modelo;
- la probabilidad asignada a esa clase;
- una respuesta visual clara, sin depender de otro servidor.

La probabilidad es la confianza interna del clasificador, no una garantía de acierto. El modelo es una demostración de NLP clásico y no debe usarse como único criterio para decisiones sensibles.

## Arquitectura

```text
Usuario
  ↓
Streamlit (app.py)
  ↓
TfidfVectorizer (unigramas + bigramas, hasta 5.000 features)
  ↓
Regresión logística multiclase
  ↓
Clase predicha + probabilidad estimada
```

La versión grupal exponía la inferencia mediante FastAPI y el frontend se conectaba a `localhost`. Esta versión carga los artefactos directamente en Streamlit y los conserva en caché durante la sesión del proceso. No requiere backend separado, secretos, descargas ni servicios externos en runtime.

## Modelo y NLP

- **Representación:** `TfidfVectorizer` de scikit-learn.
- **Features:** unigramas y bigramas, `min_df=3`, `max_df=0.9`, máximo de 5.000 términos.
- **Clasificador:** `LogisticRegression` con `class_weight="balanced"`, `C=1.0`, solver `newton-cg` y `max_iter=1000`.
- **Clases serializadas:** `Negativo`, `Neutro` y `Positivo`.
- **Persistencia:** artefactos joblib incluidos en `models/`.

No se publican métricas porque la rama de origen no conserva un reporte de evaluación reproducible junto a los artefactos. Esta versión no reentrena ni altera el modelo.

## Dataset y origen de datos

Según el código de la rama original, el entrenamiento utilizó `data/processed/dataset_unificado.csv`, producido mediante la unificación y normalización de tres CSV de `data/raw/`. Entre ellos hay un conjunto sintético multilingüe V6 generado por el equipo con reseñas en español, inglés y portugués, además de otros dos archivos identificados en esa rama como `DB_archivo_con_sentimiento.csv` y `DB_dataset_unificado.csv`.

El repositorio de portfolio no incluye los datasets ni scripts de entrenamiento porque no son necesarios para ejecutar la demo. Para revisar el pipeline original y la procedencia disponible, consulte la [rama grupal de origen](https://github.com/S4mma3l/H12-25-L-Equipo-72/tree/feature/mejora-dataset-v6). No se atribuye una fuente externa más específica cuando el proyecto original no la documenta.

## Tecnologías

- Python 3.12
- Streamlit
- scikit-learn 1.8.0
- joblib
- TF-IDF y regresión logística

`scikit-learn==1.8.0` está fijado porque esa es la versión con la que se serializaron los dos artefactos. Así se evitan advertencias y riesgos de incompatibilidad al deserializarlos.

## Estructura

```text
sentiment-ai/
├── .streamlit/
│   └── config.toml
├── models/
│   ├── sentiment_model.joblib
│   └── tfidf_vectorizer.joblib
├── app.py
├── requirements.txt
├── runtime.txt
├── README.md
├── ATTRIBUTION.md
├── LICENSE
└── .gitignore
```

## Instalación local

Requisitos: Python 3.12 y Git.

```bash
git clone https://github.com/GabArg/sentiment-ai.git
cd sentiment-ai
python -m venv .venv
```

En Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

En macOS o Linux:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Streamlit mostrará la URL local en la terminal. No hay que iniciar FastAPI ni configurar variables de entorno.

## Ejemplo de uso

1. Escribí una reseña, por ejemplo: `La atención fue excelente y el envío llegó a tiempo.`
2. Seleccioná **Analizar sentimiento**.
3. La aplicación mostrará exactamente la etiqueta producida por el modelo y su probabilidad estimada.

## Despliegue en Streamlit Community Cloud

Use esta configuración:

```text
Repository: GabArg/sentiment-ai
Branch: main
Main file path: app.py
```

No hacen falta secrets ni comandos de inicio adicionales. `runtime.txt` recomienda Python 3.12 y `requirements.txt` instala la versión compatible de scikit-learn.

## Origen y cambios de esta versión

El proyecto fue desarrollado originalmente en equipo dentro de No Country. Esta recuperación:

- elimina FastAPI y la conexión a `localhost` del camino de despliegue;
- ejecuta TF-IDF e inferencia directamente en Streamlit;
- incluye los artefactos originales en el repositorio, sin descargas en runtime;
- carga modelo y vectorizador una sola vez mediante caché;
- valida entradas y presenta errores sin tracebacks al usuario;
- rehace la interfaz con un diseño sobrio y responsive;
- reduce dependencias y documenta compatibilidad, procedencia y despliegue.

Consulte [ATTRIBUTION.md](ATTRIBUTION.md) para la atribución completa.

## Licencia

Este trabajo derivado se distribuye bajo la [GNU General Public License v3.0](LICENSE), igual que el proyecto original. Los avisos de procedencia y autoría del equipo deben conservarse al redistribuir esta versión.
