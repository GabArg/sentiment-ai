# Fase 3.3: review multilingüe estructurado

Experimento acotado y no productivo ejecutado sobre 18 comentarios manuales en inglés,
portugués e italiano. No modifica el pipeline, el router ni la UI.

## Contratos

Se usó `response_format.type=json_schema` con `strict=true`, objeto cerrado mediante
`additionalProperties=false` y sentimiento limitado a `Negativo`, `Neutro` o
`Positivo`. Nueve casos exigieron `sentiment` y un `rationale` de hasta 120 caracteres;
los otros nueve exigieron únicamente `sentiment`. `confidence` fue eliminado porque
no es una probabilidad calibrada ni participa de la decisión.

El texto se anonimizó antes de construir el request. No se enviaron etiquetas esperadas,
predicciones o confianza local, filas, CSV ni metadata.

## Resultado real

- 18 requests nuevos, secuenciales, sin retries internos.
- 13 respuestas válidas y conformes al schema; 0 JSON sintácticamente inválidos y
  0 violaciones del schema.
- 4 respuestas vacías con `finish_reason=length`: tres con límite 128 y una con 192.
- 1 HTTP 429. El proceso sobrevivió al timeout del ejecutor y continuó con su pacer;
  una reanudación preparada mientras su estado era ambiguo explica el solapamiento.
- Accuracy end-to-end: 13/18 (72.22%). Accuracy entre respuestas válidas: 13/13 (100%).
- Por idioma end-to-end: EN 50%, PT 83.33%, IT 83.33%.
- Por clase end-to-end: Negativo 50%, Neutro 66.67%, Positivo 100%.
- Textos cortos end-to-end: 5/9 (55.56%). Neutrales factuales: 4/6 (66.67%).
- Tokens: 5,113 input, 1,876 output, 6,989 total; output promedio 110.35 y máximo 192.
- Costo total observado: USD 0.00319655; USD 0.00017759 por comentario y
  USD 0.01775861 por 100 comentarios por regla de tres.
- Inferencia: min 228 ms, mediana 400 ms, P95 1,065 ms, max 2,038 ms.
  Pacing acumulado: 174.67 s; no se mezcla con la latencia anterior.

## Decisión

El schema estricto eliminó texto extra y violaciones contractuales, pero no evita que el
presupuesto de completion sea consumido antes de producir contenido visible. Los límites
128 y 192 no son robustos para `gpt-oss-120b`. El valor 256 no se probó: hacerlo habría
superado el máximo de 18 llamadas nuevas. Debe ser el primer candidato de una prueba
posterior pequeña, con un único proceso observable y un pacer que pueda recuperar su
ventana persistida.

No se recomienda promover todavía el review multilingüe directo al runtime de 3.4:
falló el criterio de cero truncamientos y quedó por debajo de 95% end-to-end. Sí queda
confirmado que, cuando el modelo entrega contenido, el contrato es estable y la calidad
del fixture fue 100%.

Los resultados auditables están en `artifacts/experiments/multilingual_phase_3_3_*`.
