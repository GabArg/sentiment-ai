# Evaluación de calidad y observabilidad

Las evaluaciones de Sentiment AI tienen procedencias, tamaños y objetivos distintos. Sus métricas se informan por separado: ninguna representa una garantía de rendimiento general o productivo.

## Síntesis de evidencia

| Evaluación | Datos y condición | Resultado observado | Limitación principal |
|---|---|---:|---|
| Holdout histórico reconstruido | split estratificado por filas del corpus de entrenamiento | ~89,42% accuracy | comparte segmentos y familias textuales entre train y test; puede ser optimista |
| Benchmark manual de 60 | 20 positivos, 20 negativos y 20 neutrales factuales en español | 51,67% accuracy; macro-F1 0,4868; recall neutro 20% | muestra pequeña y dirigida, ya consultada durante el diagnóstico |
| Demo sintético de 104 | 74 negativos, 15 positivos y 15 neutrales | 75,00% accuracy; macro-F1 0,5198; recall neutro 6,67% | sintético, desbalanceado y no independiente |
| Revisión híbrida | reproducción sobre los mismos 60 casos con resultados externos observados | 59/60, 98,33% accuracy | exploratoria; no es una validación independiente ni una métrica del modelo local |
| Revisión multilingüe directa | muestra curada de 48 casos ES/EN/PT/IT | 47/48 casos | tamaño y cobertura lingüística limitados |

Los benchmarks de 60 y 104 se conservan para diagnóstico y regresión. No deben utilizarse para seleccionar modelos, reglas o thresholds. El siguiente test de generalización debe ser humano, congelado y separado de desarrollo por procedencia y familia textual.

## Modelo local: matrices y clases

Orden de clases: Negativo, Neutro, Positivo.

Benchmark manual de 60:

```text
[[11, 4,  5],
 [11, 4,  5],
 [ 3, 1, 16]]
```

Demo sintético de 104:

```text
[[66, 0,  8],
 [10, 1,  4],
 [ 3, 1, 11]]
```

En los 104 casos, el modelo obtuvo F1 de 0,8627 para Negativo, 0,1176 para Neutro y 0,5789 para Positivo. La distribución predicha fue 79 negativos, 2 neutrales y 23 positivos. El resultado confirma una debilidad particular en neutrales factuales; no demuestra por sí solo el comportamiento sobre feedback real.

El reporte reproducible completo está en [`artifacts/experiments/sentiment_demo_104/report.md`](../artifacts/experiments/sentiment_demo_104/report.md). La auditoría del corpus y las variantes de neutralidad están en [`artifacts/experiments/neutrality_research/report.md`](../artifacts/experiments/neutrality_research/report.md).

## Confidence y margen

`confidence` es la probabilidad que `LogisticRegression.predict_proba` asigna a la clase elegida. No es la probabilidad calibrada de que la predicción sea correcta ni una garantía fuera del dominio de entrenamiento.

El evaluador también calcula la segunda clase, su probabilidad y el margen `top-1 - top-2`. Un margen pequeño indica competencia entre clases, pero uno amplio tampoco garantiza acierto. Ambos benchmarks contienen errores de alta confianza.

## Consistencia del preprocessing

El entrenamiento recuperado aplicaba antes del TF-IDF:

1. conversión de entradas no textuales a cadena vacía;
2. eliminación de caracteres fuera de letras ASCII, vocales españolas acentuadas, `ñ`, dígitos, espacios y `.,!?`;
3. colapso de espacios;
4. minúsculas y `strip`.

La inferencia actual aplica conversión a `str` y `strip`, y luego delega al vectorizador serializado. Las variantes históricas y de normalización mínima evaluadas produjeron cero cambios de clase en los benchmarks de 60 y 104, pero esos conjuntos no ejercitan todas las incompatibilidades. Por ello no se seleccionó ni integró ningún cambio.

## Reproducción

Evaluador del benchmark manual:

```bash
python -m src.evaluation
python -m src.evaluation --json evaluation.json --csv evaluation_cases.csv
```

Evaluación sintética de 104 casos:

```bash
python artifacts/experiments/sentiment_demo_104/run_evaluation.py \
  --input artifacts/experiments/sentiment_ai_demo_pareto_104.csv \
  --output-dir artifacts/experiments/sentiment_demo_104
```

Los scripts separan el texto de entrada, las predicciones y las etiquetas de referencia. `expected_sentiment` y `tema_esperado` no se usan como features. Estas ejecuciones utilizan exclusivamente el modelo local y no llaman a Cerebras.
