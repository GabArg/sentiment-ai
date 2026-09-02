# Arquitectura multilenguaje controlada (Fase 3.0A)

Las Fases 3.0B/3.0C implementan el núcleo y su integración UX/batch detrás de `ENABLE_MULTILINGUAL_SENTIMENT`, que permanece `false` por defecto. La validación real se limitó a seis traducciones controladas.

## Ruta moderna candidata (Fase 3.4)

`ENABLE_DIRECT_MULTILINGUAL_REVIEW=false` es un flag independiente. Cuando se activa,
tiene precedencia sólo para EN/PT/IT de más de cuatro tokens y para textos de hasta cuatro
tokens, cuyo idioma se marca `short_text_uncertain` sin ejecutar langdetect. Esas rutas
envían únicamente el original anonimizado a un review estructurado de una llamada, sin
traducción. Español largo conserva local/híbrido; unsupported y errores de detección
conservan el fallback actual.

El provider usa `gpt-oss-120b`, JSON Schema estricto, únicamente `sentiment` y 256 tokens.
Traducción, hybrid review y direct review comparten `ExternalRequestCoordinator` y
`HYBRID_MAX_EXTERNAL_CALLS_PER_BATCH`. La arquitectura histórica de traducción permanece
disponible cuando el nuevo flag está apagado. Esta candidata deriva de los experimentos
3.1–3.3B y todavía no se declara production-ready.

El preview controlado de Fase 3.4 ejecutó ocho casos (EN/PT/IT y dos textos breves):
8/8 respuestas válidas y correctas, `finish_reason=stop`, sin truncamientos, 429 ni
fallbacks. Consumió una llamada por comentario, 2.937 tokens y USD 0.00131795. Es una
muestra de integración, no una métrica productiva.

## Alcance y decisión del detector

El alcance inicial queda limitado a `es`, `en`, `pt` e `it`. Se incorporó `langdetect==1.0.9`, configurado una sola vez con `DetectorFactory.seed = 0`. Es pequeño (wheel cercano a 1 MB), offline, Apache 2.0 y cubre los cuatro idiomas. Su release es de 2021, el propio proyecto advierte resultados inestables en texto corto o ambiguo sin semilla, y sus scores no se exponen como probabilidades calibradas.

| Opción | Fortalezas | Riesgos | Decisión |
|---|---|---|---|
| `langdetect` | Offline, ~1 MB, cuatro idiomas, Apache 2.0 | Antiguo; débil en frases cortas; requiere semilla fija | Prototipo recomendado, sujeto al benchmark |
| `langid` | Determinista, 97 idiomas, permite restringir clases, BSD | Última release PyPI de 2016; score no comparable; mantenimiento bajo | Reserva si `langdetect` falla el gate |
| `lingua-language-detector` | Diseñado para texto corto, activo, offline, Apache 2.0 | Wheel CPython 3.12 actual de ~170 MB; impacto de arranque/deploy | No adoptar en este deploy sin medir una variante reducida |

Gate 1 medido sobre 48 casos: 95,83% global; EN/PT/IT 100%; ES 83,33%; 0 unknown, 0 unsupported y tres ejecuciones idénticas. Los errores fueron `No resolvieron mi reclamo.` (IT) y `Pésimo soporte; no vuelvo.` (PT). El import aislado tuvo mediana aproximada de 28,9 ms en cinco procesos. Supera el mínimo acordado, aunque el margen de español exige seguimiento en 3.0C.

## Contratos

`LanguageDetector.detect(text)` devuelve `LanguageDetectionResult`:

- `detected_language`, `language_name`, `supported`;
- `confidence` opcional (se omite si el proveedor no ofrece una señal interpretable);
- `provider`, `success`, `error_code`;
- `status`: `detected`, `unsupported`, `unknown` o `error`.

`TranslationProvider.translate(text, source_language, target_language="es")` devuelve `TranslationResult`:

- idiomas fuente/destino, texto original recibido y traducción;
- proveedor, modelo, éxito, latencia, error y usage opcional;
- un resultado exitoso exige traducción no vacía; un fallo nunca incluye traducción.

`CerebrasTranslationProvider` es independiente de `CerebrasSentimentReviewProvider`. Usa prompt y schema propios y rechaza JSON libre, campos inesperados, idioma fuente incoherente y resultado vacío. No hay rescate con regex. En 3.0B fue validado sólo con clientes simulados.

## Pipeline propuesto

```text
original_text
  -> detector local
  -> es: analysis_text = original_text
  -> en/pt/it: anonymize_text -> traducción a es
       -> éxito: analysis_text = translated_text
       -> fallo: analysis_text = original_text
  -> unsupported/unknown/error: analysis_text = original_text
  -> modelo local
  -> router actual
  -> second check opcional
  -> final_prediction
```

Estados de traducción: `not_needed`, `translated`, `fallback_original`, `unsupported_language`, `detection_error`. El texto original siempre permanece local y separado. `translated_text` y `analysis_text` no se exportan en CSV por defecto.

El second check recibirá el mismo `analysis_text` usado por el modelo local, anonimizado nuevamente de forma idempotente antes del envío. Esto mantiene una única semántica observable para clasificación, routing y revisión. El costo es que un error de traducción puede propagarse a ambas etapas; por eso se preservan original, detección y estado, y la calidad de traducción debe medirse antes de habilitar el flujo. En 3.0 inicial no se alternará silenciosamente al original sólo para el second check.

## Privacidad y fallback

La anonimización ocurre antes de la traducción. El proveedor recibe exclusivamente comentario anonimizado, código de idioma origen y destino. Nunca recibe fila/CSV, expected, predicción/confianza local, customer id, región, canal ni metadata de negocio.

Un fallo de detección, falta de API key, 429, timeout, JSON inválido o fallo de traducción no bloquea clasificación: se conserva el original como `analysis_text` y se registra el estado. La UI futura mostrará un mensaje humano; los códigos técnicos quedan en detalles/trazabilidad.

## Coordinación de rate limit y presupuesto

El `RatePacer` existente se inyecta en un único `ExternalRequestCoordinator`. Traducciones y second checks llaman al mismo coordinador antes de cada request; el límite Free Tier es 5 requests por 60 segundos en total, no por provider. La prueba combinada verifica que 3 traducciones y 2 reviews pasan y la sexta solicitud espera, usando reloj falso.

Se agregó `HYBRID_MAX_EXTERNAL_CALLS_PER_BATCH=25` como presupuesto global. Cada traducción y cada second check iniciado consume una unidad antes de llamar al provider. Migración compatible:

1. si existe la nueva variable, manda el límite global;
2. si no existe y multilenguaje está ON, `HYBRID_MAX_REVIEWS_PER_BATCH` actúa como alias del límite global;
3. con multilenguaje OFF, el comportamiento actual de budget de reviews permanece idéntico.

Cuando se agota, no se hace la llamada: traducción usa `fallback_original`; review usa el fallback local existente. La salida registra `external_budget_exceeded` sin ocultarlo.

## Benchmark manual de 48 casos

`tests/fixtures/multilingual_sentiment_benchmark.csv` contiene 12 casos por idioma y, dentro de cada idioma, 4 positivos, 4 negativos y 4 neutros. Incluye producto, entrega, soporte, hechos, negaciones, cantidades y lenguaje coloquial. Los labels y textos fueron curados manualmente; no se generaron expected labels con un LLM.

Las métricas de 3.0B/3.0C serán:

- detector: accuracy por idioma, unknown/error, repetibilidad e import time;
- traducción: preservación manual de negación, polaridad, hechos, números y ausencia de invenciones;
- sentimiento: A) local directo, B) traducción→local, C) traducción→híbrido, global/idioma/clase.

## Llamadas, costo y doble llamada

El benchmark completo tiene 36 textos no españoles: una pasada de traducción completa costaría 36 llamadas, más los second checks que solicite el router. Un texto no español revisado puede consumir dos llamadas. La prueba real inicial queda limitada a 6 traducciones (2 EN, 2 PT, 2 IT). A 5 RPM, la sexta requiere esperar la siguiente ventana; la duración mínima por pacing supera aproximadamente un minuto, sin contar latencia de red.

El costo de traducción todavía es desconocido y debe calcularse con usage real. Como referencia no contractual, si cada traducción costara lo mismo que el review observado (USD 0.00017804), 6 costarían ~USD 0.00106824 y 36 ~USD 0.00640944. No se usará esa equivalencia como predicción de precio.

Una llamada combinada futura podría devolver traducción y sentimiento para textos derivados, reduciendo costo y latencia. No se implementa inicialmente: acopla contratos, dificulta atribuir fallos y sólo ahorra cuando el router revisa. Primero se medirá la arquitectura separada y modular.

## Riesgos y subfases

- Detección ambigua en textos cortos o con marcas/nombres propios.
- Confusión entre español, portugués e italiano por cercanía léxica.
- Traducción que altera negación, intensidad o factualidad.
- Doble consumo de rate/budget y mayor latencia.
- Reconstrucción de PII por el traductor; por eso no se exporta traducción y se anonimiza antes.
- Sobreajuste al fixture pequeño; no representa calidad productiva.
- `langdetect` tiene mantenimiento limitado; la dependencia debe quedar detrás de interfaz.

3.0B implementó detector, feature flag OFF, provider estructurado, pipeline y coordinador/presupuesto con mocks. 3.0C conectó UX y batch, agregó AppTest de presentación y ejecutó seis traducciones reales después del gate de QA. El histórico se toma como intención arquitectónica (traducción Cerebras/Llama 3 y revisión por incertidumbre), no como código reproducido literalmente; el diseño moderno usa gpt-oss-120b, separación de providers, feature flags, privacidad y observabilidad.
