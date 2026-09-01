# Clasificación híbrida experimental

Esta fase crea una arquitectura paralela para medir un segundo chequeo sin modificar `predict_one()`, `predict_batch()` ni la predicción visible en Streamlit. No se hicieron llamadas reales a Cerebras y el resultado híbrido no es todavía el resultado oficial del producto.

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

La UI todavía no llama este proveedor. Cuando se evalúe su activación, deberá informar que el modelo local procesa primero, sólo algunos textos son candidatos, existe anonimización parcial y el procesamiento externo es opcional.

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

- No se midió todavía la calidad real de Cerebras sobre las 60 frases.
- El resultado híbrido sólo puede considerarse mejor después de una evaluación controlada con respuestas reales o un conjunto etiquetado independiente.
- Confidence y margen no equivalen a probabilidad de error.
- El benchmark actual tiene alto coverage de revisión, con implicaciones futuras de costo, latencia y privacidad.
- No se activó traducción, detección de idioma, OOD ni neutralidad factual automática.
