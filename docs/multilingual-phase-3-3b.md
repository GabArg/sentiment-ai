# Fase 3.3B: recuperación con contrato mínimo y 256 tokens

Prueba experimental, no productiva, limitada a los cinco casos fallidos de Fase 3.3.
Se reutilizaron los trece resultados válidos anteriores sin repetir llamadas.

## Configuración y privacidad

- Modelo `gpt-oss-120b`, `max_retries=0`, ejecución secuencial.
- `max_completion_tokens=256` en las cinco llamadas.
- Schema estricto: objeto cerrado con un único campo requerido `sentiment`, limitado al
  enum `Negativo`, `Neutro`, `Positivo`.
- Sin `confidence` ni `rationale`.
- El texto original se anonimizó antes del request. No se enviaron expected labels,
  predicciones locales, idioma, metadata, filas ni CSV.

## Resultado

Los casos recuperados fueron `en-neg-r`, `en-neg-s`, `en-neu-s`, `pt-neg-s` e
`it-neu-s`. Las cinco respuestas terminaron con `finish_reason=stop`, cumplieron el
schema y fueron correctas. No hubo truncamientos, JSON inválido, violaciones del schema,
errores del proveedor ni HTTP 429.

- Tokens: 1,359 input, 645 output, 2,004 total.
- Output por llamada: 72, 172, 154, 83 y 164 tokens. Dos resultados necesitaron más
  de 128 tokens, confirmando directamente que ese límite era insuficiente.
- Costo total: USD 0.00095940; promedio USD 0.00019188 por comentario.
- Fase 3.3 `sentiment_only` a 128 usó en promedio 111.5 output tokens y costó
  USD 0.00017843 por llamada con usage: 256 incrementó el costo promedio alrededor de
  7.5%, a cambio de recuperar robustez en esta muestra.
- Latencia de inferencia: min 322 ms, mediana 404 ms, max 1,871 ms.
- Espera inicial por ventana: 0 s; pacing durante llamadas: 0 s; duración total: 3.41 s.

## Interpretación

El resultado reconstruido es 18/18: trece respuestas históricas válidas de Fase 3.3 y
cinco reintentos de Fase 3.3B. No fue una ejecución continua de dieciocho requests.

El gate de promoción experimental se cumple para avanzar a una Fase 3.4 controlada detrás
de feature flag. Cinco casos no constituyen un benchmark definitivo: deben conservarse el
fallback y la observabilidad de `finish_reason`, usage, 429 y errores del proveedor.

La cobertura de 67% informada en 3.3 fue un cambio de medición: se ejecutó
`--cov=src --cov=scripts`, incorporando scripts históricos y runners externos no cubiertos.
Con el comando documentado del proyecto, `pytest --cov=src`, la cobertura permanece en 89%.
