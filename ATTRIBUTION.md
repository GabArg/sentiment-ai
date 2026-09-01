# Atribución y procedencia

## 1. Proyecto grupal original

Sentiment AI nació como **H12-25-L-Equipo-72**, un proyecto colaborativo de No Country.

- Repositorio original: https://github.com/S4mma3l/H12-25-L-Equipo-72
- Continuación histórica/documental: https://github.com/neldyvelasquez/H12-25-L-Equipo-72
- Rama recuperada: `feature/mejora-dataset-v6`
- Commit de origen de V6: `a3a4014fb0d03b3a1ff205d0784d710344967b75`
- Licencia original: GNU General Public License v3.0

El código, pipeline de entrenamiento, datos preparados, artefactos, backend FastAPI y frontend Streamlit originales fueron trabajo del equipo. No se presentan como creación exclusiva de quien mantiene este portfolio.

### Integrantes identificados históricamente

- Carlos Mauricio Rondón
- Juan Carlos Vanegas Molina
- Javier Cañete
- Guido Arturo Broccoli
- Neldy Rolando Velásquez Samolo
- Ángel Hernández
- Yeikol Alberto Zúñiga Vargas
- José Julián Gómez Brizuela
- Lupita Baioli/Bailón (el apellido aparece con ambas grafías en la documentación)
- Griselda González
- Omar Osuna Hernández

La inclusión en esta lista acredita pertenencia documentada al equipo, no autoría individual de una funcionalidad. No se asignan usernames ni roles cuando la evidencia pública no permite verificarlos. Sí se identifican públicamente `S4mma3l` con Ángel Hernández, `neldyvelasquez` con Neldy Rolando Velásquez Samolo y `GabArg` con Guido Arturo Broccoli según los repositorios y documentación histórica revisados.

## 2. Recuperación técnica V6 para portfolio

La primera versión de `GabArg/sentiment-ai` recuperó los artefactos V6 sin reentrenarlos y preparó una demo independiente:

- sustituyó el runtime Streamlit → FastAPI/localhost por inferencia local;
- incluyó `sentiment_model.joblib` y `tfidf_vectorizer.joblib`;
- añadió caché, validación y asociación correcta de clases/probabilidades;
- redujo dependencias y documentó compatibilidad y despliegue.

## 3. Evolución v2 posterior

La branch `feature/v2-dashboard-ai-report` contiene una implementación nueva realizada posteriormente en este repositorio, inspirada en capacidades descritas en la documentación histórica, no una reconstrucción ficticia del código final perdido. Incluye:

- arquitectura modular e inferencia batch vectorizada;
- carga y validación CSV;
- dashboard y métricas de negocio;
- extracción determinística de temas negativos y Pareto 80/20;
- informe ejecutivo determinístico;
- contexto minimizado, anonimización e informe opcional con Cerebras;
- fallback, exportaciones y suite de tests.

## Participación de Guido

### En el proyecto original

La evidencia documental permite afirmar que **Guido Arturo Broccoli (`GabArg`)** fue miembro activo, participó en varias reuniones, preparó y corrigió el guion del video final y trabajó en la narrativa de alcance, validación y cierre. La evidencia Git pública disponible no permite atribuirle originalmente frontend, backend, modelo o dashboard; por eso no se hace esa afirmación.

### En la evolución para portfolio

El historial de `GabArg/sentiment-ai` documenta la recuperación técnica V6 y la nueva implementación v2 enumerada arriba. Esta autoría posterior se distingue explícitamente del trabajo grupal original.

## Licencia

Esta obra derivada continúa bajo **GNU General Public License v3.0**. El texto completo está en `LICENSE`. Toda redistribución o modificación debe cumplir GPL-3.0 y conservar los avisos aplicables de origen y modificación.
