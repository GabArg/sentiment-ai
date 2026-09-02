# Validación multilenguaje controlada (Fase 3.0C)

El modo multilenguaje es experimental, opt-in y permanece desactivado por defecto. Soporta inicialmente español, inglés, portugués e italiano. La detección ocurre localmente con `langdetect==1.0.9`; la traducción opcional usa Cerebras `gpt-oss-120b` después de anonimizar el comentario.

## Integración

Con `ENABLE_MULTILINGUAL_SENTIMENT=false`, la aplicación conserva el flujo y schema anteriores. Con el flag activo, la UI individual separa idioma/traducción del estado de revisión de sentimiento. El batch preserva columnas originales y agrega trazabilidad de idioma y traducción; no exporta `translated_text` ni `analysis_text`.

Traducciones y second checks comparten un único `ExternalRequestCoordinator`, configurado inicialmente a 5 requests por 60 segundos, y un presupuesto global `HYBRID_MAX_EXTERNAL_CALLS_PER_BATCH=25`.

## Límites del detector

El benchmark manual de 48 casos obtuvo 95,83% global: EN/PT/IT 100% y ES 83,33%. La detección puede ser menos fiable en textos breves o ambiguos. En particular, dos frases españolas cortas fueron confundidas con italiano y portugués. No se añadieron heurísticas específicas para corregirlas.

## Prueba real de seis traducciones

Se ejecutaron seis traducciones secuenciales: dos inglesas, dos portuguesas y dos italianas. Las seis respetaron el contrato JSON y conservaron significado, polaridad y hechos/fecha. El set no contenía negaciones, por lo que esa dimensión no quedó validada.

Resultados observados, no generalizables:

- detección: 6/6;
- traducción exitosa: 6/6;
- local sobre original: 4/6 (66,67%);
- local sobre traducción: 3/6 (50%);
- híbrido final: 6/6, con cinco reviews exitosos y un fallback local;
- traducción mejoró un caso local y degradó dos; tres neutrales traducidos fueron clasificados localmente como negativos.

Usage de traducción: 1.117 input tokens, 732 output tokens, 1.849 total. Con precios públicos consultados para `gpt-oss-120b` de USD 0,35/M input y USD 0,75/M output, el costo estimado fue USD 0,00093995, promedio USD 0,00015666 por traducción.

Los cinco reviews exitosos reportaron 1.442 input tokens, 544 output tokens y 1.986 total, con costo estimado USD 0,00091270. El request fallido no reportó usage, por lo que ese costo no está incluido.

Latencia de traducción: mínimo 841 ms, mediana 995 ms, máximo 2.371 ms. Latencia de review: mínimo 770 ms, mediana 1.043 ms, máximo 1.979 ms. El pacing acumuló aproximadamente 109,7 segundos de espera en una ejecución total de 126,4 segundos.

La traducción preservó correctamente el significado en esta muestra, pero no mejoró por sí sola el clasificador local. La siguiente evaluación debe ampliar neutrales/factuales y negaciones antes de considerar el modo listo para producción.

## Activación manual

```toml
ENABLE_MULTILINGUAL_SENTIMENT = true
CEREBRAS_API_KEY = "..."
```

`ENABLE_HYBRID_SENTIMENT` sigue siendo independiente. No debe incluirse una API key real en el repositorio.
