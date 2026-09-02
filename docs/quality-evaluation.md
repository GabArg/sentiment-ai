# Evaluación de calidad y observabilidad

El benchmark versionado en `tests/fixtures/sentiment_benchmark.csv` contiene 60 casos manuales en español: 20 opiniones positivas, 20 opiniones negativas y 20 enunciados factuales neutrales. Es exclusivamente un conjunto de evaluación; no debe incorporarse al entrenamiento ni usarse para seleccionar ejemplos que oculten errores.

## Dos contextos de evaluación

- **Holdout in-domain reconstruido:** el split estratificado documentado del corpus original alcanza aproximadamente 89,42 % de accuracy. Mide generalización dentro de la mezcla de fuentes utilizada para entrenar.
- **Benchmark externo/manual:** los artefactos actuales alcanzan 51,67 % global y 20 % en Neutro sobre estas 60 frases. Esta cifra describe únicamente este benchmark pequeño y dirigido; no es una métrica general del modelo.

El benchmark está pensado como instrumento de regresión y diagnóstico. Los tests verifican su integridad y la reproducibilidad del cálculo, pero deliberadamente no exigen un accuracy mínimo.

## Confidence y margen

`confidence` es la probabilidad que `LogisticRegression.predict_proba` asigna a la clase elegida. No es una probabilidad de que la predicción sea correcta ni una garantía calibrada fuera del dominio de entrenamiento.

El módulo también calcula la segunda clase, su probabilidad y el margen `top-1 - top-2`. Un margen pequeño indica competencia entre clases, pero un margen amplio tampoco garantiza acierto. El benchmark contiene errores con confidence igual o superior a 80 %, por lo que 80 % no debe interpretarse como certeza ni utilizarse aisladamente como regla de calidad.

## Ejecución y exportación

```bash
python -m src.evaluation
python -m src.evaluation --json evaluation.json --csv evaluation_cases.csv
```

La salida incluye métricas globales y por clase, matriz de confusión, confianza, casos bajo 80 %, errores de alta confianza, distribución de márgenes y detalle por caso.

## Consistencia de preprocessing

El entrenamiento recuperado aplicaba antes del TF-IDF:

1. conversión de entradas no textuales a cadena vacía;
2. eliminación de caracteres fuera de letras ASCII, vocales españolas acentuadas, `ñ`, dígitos, espacios y `.,!?`;
3. colapso de espacios;
4. minúsculas y `strip`.

La inferencia v2 sólo aplica conversión a `str` y `strip`; después delega al vectorizador serializado. El vectorizador sí convierte a minúsculas y tokeniza, pero no replica la regex histórica ni el colapso previo. La diferencia es demostrable: el entrenamiento convertía `excelente-servicio` en `excelenteservicio`, mientras la inferencia actual tokeniza el texto crudo como palabras separadas.

Corregir esta diferencia alteraría vectores y predicciones existentes. Por eso Fase 1 sólo la documenta y añade un test reproducible; no cambia el pipeline de inferencia ni los `.joblib`.
