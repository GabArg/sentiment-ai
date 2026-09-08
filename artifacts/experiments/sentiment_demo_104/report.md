# Evaluación offline — Sentiment Demo 104

> Dataset sintético de evaluación. No se utilizó para entrenamiento, selección de modelo ni ajuste de thresholds.

## Reproducibilidad

- Fuente: `artifacts\experiments\sentiment_ai_demo_pareto_104.csv`
- SHA-256: `16610c4e3aaa601c09fbf32e47baaceef7f39b3eff75f5bac8fe0b2a7356a206`
- Feature enviada al modelo: `comentario` exclusivamente.
- `expected_sentiment` se incorporó únicamente después de generar predicciones.
- `tema_esperado` no fue utilizado por el modelo ni por esta evaluación de sentimiento.
- Modelo: artefactos locales congelados TF-IDF + regresión logística.

## Métricas globales

- Accuracy: **0.7500**
- Macro-F1: **0.5198**
- Weighted-F1: **0.7143**
- Errores: **26 / 104**

| Clase | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| Negativo | 0.8354 | 0.8919 | 0.8627 | 74 |
| Neutro | 0.5000 | 0.0667 | 0.1176 | 15 |
| Positivo | 0.4783 | 0.7333 | 0.5789 | 15 |

## Matriz de confusión

Filas = referencia; columnas = predicción.

| Referencia \ Predicción | Negativo | Neutro | Positivo |
|---|---:|---:|---:|
| Negativo | 66 | 0 | 8 |
| Neutro | 10 | 1 | 4 |
| Positivo | 3 | 1 | 11 |

## Distribución

| Clase | Esperada | Predicha |
|---|---:|---:|
| Negativo | 74 | 79 |
| Neutro | 15 | 2 |
| Positivo | 15 | 23 |

## Confianza local

- Media en aciertos: 0.6923
- Media en errores: 0.5667
- Errores con confidence ≥ 0.80: 1

## Flujos de error

| Esperada | Predicha | Casos |
|---|---|---:|
| Neutro | Negativo | 10 |
| Negativo | Positivo | 8 |
| Neutro | Positivo | 4 |
| Positivo | Negativo | 3 |
| Positivo | Neutro | 1 |

## Neutrales factuales

- Casos: 15
- Aciertos: 1
- Accuracy: 0.0667
- Distribución predicha: {'Negativo': 10, 'Neutro': 1, 'Positivo': 4}

## Negaciones

- Detección para auditoría: `Regex lexical audit: \b(?:no|nunca|nadie|sin|tampoco|ni|jam[aá]s)\b`
- Casos detectados: 42
- Aciertos: 41
- Errores: 1
- Accuracy: 0.9762

## Ejemplos representativos de errores

Selección determinística: error de mayor confianza por cada flujo referencia→predicción.

| case_id | Comentario | Esperada | Predicha | Confidence |
|---|---|---|---|---:|
| DEMO-054 | La devolución se resolvió rápidamente y recibí el reintegro sin problemas. | Positivo | Negativo | 0.9284 |
| DEMO-010 | El modelo corresponde a la versión publicada este año. | Neutro | Negativo | 0.7491 |
| DEMO-013 | El envío tardó mucho más de lo informado al comprar. | Negativo | Positivo | 0.7065 |
| DEMO-087 | La compra incluye dos unidades y un accesorio adicional. | Neutro | Positivo | 0.6682 |
| DEMO-061 | El precio fue conveniente y el producto superó mis expectativas. | Positivo | Neutro | 0.5337 |

## Limitaciones

- Las etiquetas son sintéticas y este conjunto no representa por sí solo producción.
- La auditoría de negaciones es léxica; no garantiza que toda construcción negativa haya sido detectada.
- Confidence es la probabilidad de la clase elegida por el modelo local, no una probabilidad calibrada de acierto.
- Este resultado no autoriza modificar thresholds ni seleccionar un modelo sobre los mismos 104 casos.
