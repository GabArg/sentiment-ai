# Clasificación híbrida experimental

## Fase 2.2: modo controlado y opt-in

La UI conserva el comportamiento local por defecto. El flujo controlado sólo se habilita explícitamente con:

```toml
ENABLE_HYBRID_SENTIMENT = true
```

Los thresholds exploratorios por clase local son:

```text
Negativo < 0.80
Neutro   < 0.65
Positivo < 0.60
```

El operador es estrictamente `<`. Estos valores fueron seleccionados y evaluados sobre el mismo benchmark manual de 60 casos: no son una calibración productiva. La configuración puede volver al baseline global de 0,80 mediante `ReviewRouterConfig` o desactivarse completamente con el feature flag.

### Estados y consolidación

- `local_only`: no se solicitó revisión; el resultado final es local.
- `review_requested`: transición auditable previa al proveedor.
- `reviewed`: second check válido y misma clase.
- `disagreement`: second check válido y clase distinta; el resultado final usa la revisión.
- `fallback_local`: falta de key, timeout, 429, error, respuesta inválida o budget agotado; conserva la clase local.

El resultado estructurado conserva predicción/confianza/margen local, reasons, proveedor/modelo, latencia, error y si se utilizó fallback. La confidence declarada por Cerebras no decide la consolidación y no se muestra como certeza.

### Individual, batch y latencia

El modo individual construye el proveedor con `max_retries=0` para evitar esperas opacas causadas por retries internos. Un error produce fallback local y una advertencia segura, sin traceback.

El batch es secuencial, usa `max_retries=1` como máximo y aplica pacing desacoplado: cinco requests por ventana de 60 segundos, con reloj y sleeper inyectables para tests. La UI muestra progreso y espera de ventana. El límite inicial es `HYBRID_MAX_REVIEWS_PER_BATCH=25`; los candidatos restantes se marcan `fallback_local` con `review_budget_exceeded`.

Antes de ejecutar el batch se muestran cantidad prevista y costo orientativo usando USD 0,000178 por review, observado en una validación puntual. El costo real depende de tokens, modelo y precios.

### Privacidad y separación de proveedores

La clasificación local siempre ocurre primero. Sólo el texto del comentario derivado pasa por `anonymize_text`, que reemplaza emails, teléfonos, URLs e IDs largos. No se envían expected labels, predicciones locales, otras columnas ni filas completas. El second check y el informe ejecutivo mantienen prompts, estados, flags y acciones separados; habilitar el híbrido no genera un informe IA.

### Benchmark y rollback

En el benchmark manual versionado, el router por clase deriva 43/60 casos, captura 26 de 29 errores y alcanza un 95% híbrido al reproducir los resultados externos observados. Es evidencia exploratoria, no una métrica de producción. Rollback: establecer `ENABLE_HYBRID_SENTIMENT=false`; no requiere cambiar modelo, artefactos, preprocessing ni columnas locales existentes.

La arquitectura preserva `predict_one()` y `predict_batch()`. Hubo validaciones reales controladas con Cerebras, pero el resultado híbrido sólo reemplaza la predicción visible cuando el feature flag experimental se habilita explícitamente; no es el default productivo.

## Arquitecturas y evidencia

### v2 pública actual

```text
texto -> TF-IDF -> LogisticRegression -> predicción local visible
```

### histórica confirmada

La evidencia recuperada confirma modelo local, baseline de confianza de 80 %, segunda revisión con Cerebras/Llama 3 y clasificación ternaria. El código, prompt, modelo exacto y consolidación históricos no están disponibles.

### v2 experimental moderna

```text
texto -> modelo local -> observabilidad -> router de incertidumbre
                                      ├─ no revisar -> local_only
                                      └─ revisar -> texto anonimizado
                                                   -> proveedor estructurado
                                                   -> comparación/fallback
```

La v2 usa el modelo Cerebras configurado actualmente por el proyecto (`gpt-oss-120b`). No afirma usar ni reconstruir el Llama 3 histórico.

## Router experimental

Reglas numéricas automáticas y auditables:

- `low_confidence`: `local_confidence < confidence_threshold`; el valor 0,80 se conserva como baseline histórico, no como verdad estadística.
- `small_margin`: `prediction_margin < margin_threshold`; deshabilitada por defecto porque el benchmark no justifica elegir un threshold final.

La interfaz admite `possible_factual_neutral`, `possible_out_of_domain` y `language_mismatch` como señales explícitas de futuros detectores. No se generan automáticamente: aún no existe una definición robusta y validada. No hay reglas léxicas como días de la semana.

## Evaluación exploratoria del router

Sobre las 60 frases manuales, el baseline `<0,80` revisa 50 casos (83,33 %), captura 28 de 29 errores locales, deja escapar uno, envía 22 aciertos innecesariamente y tiene precision de router de 56 %.

Agregar alternativamente margen `<0,05`, `<0,10`, `<0,15`, `<0,20`, `<0,25` o `<0,30` no cambia ninguna métrica: todos esos casos ya estaban incluidos por baja confianza. Por lo tanto, este benchmark no aporta evidencia para seleccionar un margen definitivo.

Estas 60 frases son un benchmark exploratorio pequeño y dirigido. No deben utilizarse como conjunto suficiente para calibrar producción ni optimizar repetidamente thresholds.

Ejecutar:

```bash
python -m src.router_evaluation
```

## Contrato del proveedor

`SentimentReviewProvider.review_sentiment(text)` devuelve `ReviewResult`:

- sentimiento exclusivamente `Negativo`, `Neutro` o `Positivo`;
- confidence opcional entre 0 y 1;
- rationale opcional y breve;
- provider y model;
- success y error_code;
- uso de tokens cuando el SDK lo expone.

El prompt `sentiment-review-v1` define Neutro como información factual, descripción sin opinión, estado objetivo o ausencia de valoración clara. Exige JSON y no solicita negocio, recomendaciones ni planes de acción. Este prompt es independiente del informe ejecutivo.

## Privacidad

El informe ejecutivo continúa enviando sólo agregados. Un second check cambia la superficie de privacidad porque necesita texto.

Antes del proveedor se reemplazan email, teléfono, URL e IDs largos. No se envían filas, CSV, canal, región, segmento ni otras columnas. No se anonimizaron nombres propios porque una heurística no validada podría destruir significado y dar una falsa garantía de privacidad; queda como riesgo explícito.

La UI sólo llama este proveedor cuando el feature flag opt-in está habilitado. Informa que el modelo local procesa primero, sólo algunos textos son candidatos, existe anonimización parcial y el procesamiento externo es opcional.

## Fallback y estados

- `local_only`: el router no solicitó revisión.
- `review_requested`: transición lógica representada por `review_requested=True`.
- `reviewed`: proveedor válido y misma clase local.
- `disagreement`: proveedor válido y clase distinta.
- `fallback_local`: falta de key, timeout, 429, error o respuesta inválida; conserva la clase local.

Sin `CEREBRAS_API_KEY`, la aplicación y los tests siguen funcionando. Una revisión solicitada queda `provider_status=unavailable`, `state=fallback_local`; nunca se presenta como validada por IA.

## Prueba manual futura

No ejecutar como parte del QA automático. Con una key configurada:

```bash
python -m scripts.manual_sentiment_review --text "El pedido llegó el martes."
```

Admite entre 1 y 10 `--text`. No imprime la API key. Si se usa `--output`, guarda sólo índice, clasificación, estado, proveedor/modelo y uso de tokens; no persiste el texto.

## Limitaciones

- La validación controlada observó 50/50 aciertos de Cerebras sobre los casos derivados por el baseline, pero ese resultado pequeño no garantiza calidad futura.
- El resultado híbrido sólo puede considerarse mejor después de una evaluación controlada con respuestas reales o un conjunto etiquetado independiente.
- Confidence y margen no equivalen a probabilidad de error.
- El benchmark actual tiene alto coverage de revisión, con implicaciones futuras de costo, latencia y privacidad.
- No se activó traducción, detección de idioma, OOD ni neutralidad factual automática.
