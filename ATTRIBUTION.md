# Atribución y procedencia

## Proyecto grupal original

Sentiment AI nació como **H12-25-L-Equipo-72**, un proyecto colaborativo de No Country.

### Integrantes que participaron activamente en el proyecto

- Carlos Mauricio Rondón
- Juan Carlos Vanegas Molina
- Guido Arturo Broccoli
- Neldy Rolando Velásquez Samolo
- José Julián Gómez Brizuela

El código, el pipeline de entrenamiento, los datos preparados, los artefactos y las primeras implementaciones fueron resultado del trabajo grupal. No se asignan aquí roles técnicos individuales cuando la evidencia disponible no permite verificarlos con suficiente precisión.

La documentación histórica contenía referencias a otras personas asociadas al espacio o al equipo, pero no se las acredita aquí como participantes efectivos del proyecto.

### Evidencia técnica histórica

- Repositorio original: https://github.com/S4mma3l/H12-25-L-Equipo-72
- Continuación histórica/documental: https://github.com/neldyvelasquez/H12-25-L-Equipo-72
- Rama recuperada: `feature/mejora-dataset-v6`
- Commit de origen de V6: `a3a4014fb0d03b3a1ff205d0784d710344967b75`
- Licencia original: GNU General Public License v3.0

Estas referencias acreditan la procedencia de repositorios, ramas y commits. No equivalen por sí mismas a participación efectiva en el desarrollo grupal. La cuenta `S4mma3l`, asociada en la documentación histórica a Ángel Hernández, se conserva como fuente técnica histórica del repositorio original. Esa evidencia técnica se documenta por separado y no se lo incluye entre los integrantes cuya participación activa se acredita en esta versión.

## Recuperación técnica V6 para portfolio

La primera versión de `GabArg/sentiment-ai` recuperó los artefactos V6 sin reentrenarlos y preparó una demo independiente:

- reemplazó el flujo Streamlit → FastAPI/localhost por inferencia local;
- incorporó `sentiment_model.joblib` y `tfidf_vectorizer.joblib`;
- añadió caché, validación y asociación correcta de clases y probabilidades;
- redujo dependencias y documentó compatibilidad y despliegue.

Esta recuperación reutiliza una base histórica grupal y se distingue de la autoría del proyecto original.

## Evolución v2 posterior

La evolución v2 fue desarrollada posteriormente en este repositorio. Está inspirada en capacidades descritas en la documentación histórica, pero no pretende reconstruir literalmente una implementación final que no está disponible. Incluye:

- arquitectura modular e inferencia local y batch;
- carga, validación y exportación CSV;
- dashboard, métricas de negocio, temas negativos y Pareto 80/20;
- informe ejecutivo determinístico y redacción IA opcional;
- revisión híbrida estructurada y fallback observable;
- arquitectura multilingüe experimental y direct structured review para ES/EN/PT/IT;
- anonimización, minimización de datos, budget y pacing compartido;
- evaluación reproducible, tests automatizados, CI y documentación técnica;
- preparación de la release candidate `v2.0.0-rc1`.

## Participación de Guido

### En el proyecto original

La evidencia documental permite afirmar que **Guido Arturo Broccoli (`GabArg`)** fue miembro activo del equipo, participó en reuniones y colaboró en la narrativa, validación y cierre del proyecto, incluida la preparación y corrección del guion del video final. No se le atribuyen componentes históricos específicos —como frontend, backend, modelo o dashboard— cuando esa autoría individual no está demostrada.

### En la recuperación y evolución para portfolio

El historial de `GabArg/sentiment-ai` documenta el trabajo posterior de recuperación técnica, evaluación del modelo, arquitectura v2, analytics, revisión híbrida, experimentación multilingüe, privacidad, testing, CI, documentación y preparación de la release candidate. Esta contribución posterior se presenta separadamente del trabajo grupal original.

## Licencia

Esta obra derivada continúa bajo **GNU General Public License v3.0**. El texto completo está en [LICENSE](LICENSE). Toda redistribución o modificación debe cumplir GPL-3.0 y conservar los avisos aplicables de origen y modificación.
