# Fase 3.5 — Validation Gate

Fixture manual congelado de 48 casos. SHA256:
`0310071e989f6f447ef697a77d2c9f9b1f7f9dc0ce95bdcc2d0e68e6fb01d417`.
Incluye 12 casos largos por EN/PT/IT y 12 textos breves (3 ES/EN/PT/IT), con 16
casos por clase. El benchmark usó sin cambios la ruta productiva candidata de Fase 3.4,
el provider estructurado a 256 tokens y `ExternalRequestCoordinator` a 5 RPM.

## Resultado

- Accuracy end-to-end: 47/48 (97.92%).
- EN largo: 12/12; PT largo: 11/12; IT largo: 12/12.
- Negativo: 16/16; Neutro: 15/16; Positivo: 16/16.
- Neutrales globales: 93.75%; neutrales factuales: 100%.
- Negaciones: 83.33%; contrastes: 100%; textos breves: 12/12.
- 46/48 structured outputs válidos, todos con `finish_reason=stop`.
- Cero truncamientos y cero errores JSON/schema.
- Dos HTTP 429 en posiciones 10 y 35; el fallback local coincidió con expected en ambos,
  pero cuentan como fallos de provider. No se repitieron.
- Único error semántico: `pt-hard-03`, “A entrega não chegou atrasada; veio no horário
  previsto.” Expected Neutro, obtenido Positivo, categoría negación.

Tokens: 12.810 input, 3.721 output, 16.531 total. Costo observado USD 0.00727425,
USD 0.00015155 por comentario end-to-end; regla de tres: USD 0.01515469/100 y
USD 0.15154688/1.000. Latencia de inferencia: min 700 ms, mediana 857 ms, P95
1.114 ms, max 2.549 ms. Pacing acumulado 502.35 s y duración 547.19 s. A 5 RPM,
100 comentarios requieren aproximadamente 1.200 s (20 minutos), dominados por RPM.

## Decisión

Gate **FAIL**. Accuracy, idiomas, short texts, neutrales, schema y truncamiento superaron
los mínimos, pero provider success fue 95.83%, por debajo de 98%. No se promueve todavía
como arquitectura multilingüe principal. Los puntos débiles acotados son resiliencia
operativa del pacing frente al límite remoto y una interpretación de negación neutral en
portugués. No se cambió ni reejecutó el benchmark.
