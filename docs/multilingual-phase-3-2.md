# Fase 3.2: traducción previa vs review multilingüe directo

Evaluación experimental sin cambios de runtime. Todos los resultados se persistieron antes de imprimir el resumen en `artifacts/experiments/`.

## Diseño y llamadas

Completar A y B sobre 12 casos podía consumir hasta 36 llamadas. Se priorizó B completa sobre 12 casos y una muestra pareada A de 9 casos (3 por idioma: negativo, neutral y contraste positivo). Máximo previo: 30; llamadas ejecutadas: 30.

- A: 9 traducciones + 9 reviews sobre traducido = 18 llamadas, 2 por comentario.
- B: 12 reviews directos sobre original anonimizado = 12 llamadas, 1 por comentario.
- Modelo: `gpt-oss-120b`; secuencial, `max_retries=0`, pacer único 5 RPM.

## Calidad

| Métrica | Arquitectura A | Arquitectura B |
|---|---:|---:|
| Casos | 9 pareados | 12 |
| Accuracy end-to-end | 9/9 (100%) | 11/12 (91,67%) |
| Accuracy sobre respuestas válidas | 9/9 | 11/11 (100%) |
| Accuracy B en los 9 pareados | — | 8/9 (88,89%) |
| Fallos externos | 0 | 1 `invalid_json` |
| Accuracy local traducido antes del review | 3/9 (33,33%) | No aplica |

En A, las nueve traducciones solicitaron review. El local acertó los tres negativos y falló los tres neutrales y los tres contrastes; los reviews corrigieron los seis errores. En B, todas las respuestas válidas fueron correctas por clase. El fallo fue un neutral italiano.

## Negaciones

| Original | Traducción | Expected | Local traducido | A final | B final |
|---|---|---|---|---|---|
| The service was not disappointing. | El servicio no fue decepcionante. | Positivo | Negativo | Positivo | Positivo |
| O serviço não foi decepcionante. | El servicio no fue decepcionante. | Positivo | Negativo | Positivo | Positivo |
| Il servizio non è stato deludente. | El servicio no ha sido decepcionante. | Positivo | Negativo | Positivo | Positivo |

Las traducciones preservaron la negación y polaridad semántica. El modelo local invirtió los tres contrastes; ambos tipos de review los clasificaron correctamente.

## Costo y latencia

Precios usados: USD 0,35/M input tokens y USD 0,75/M output tokens.

| Arquitectura | Input | Output | Costo total | Costo/comentario | Latencia externa media/comentario |
|---|---:|---:|---:|---:|---:|
| A | 4.242 | 2.064 | USD 0,00303270 | USD 0,00033697 | 859 ms |
| B | 3.453 | 1.517 | USD 0,00234630 | USD 0,00019552 | 480 ms |

B redujo aproximadamente 42% el costo por comentario y 44% la latencia externa sin pacing. A 5 RPM, A requiere el doble de solicitudes. La corrida combinada esperó 290,5 segundos por pacing y duró 304,1 segundos.

Por regla de tres para 100 comentarios no españoles:

- A: 200 llamadas, ~USD 0,033697, al menos unas 39 esperas de ventana tras las primeras cinco llamadas.
- B: 100 llamadas, ~USD 0,019552, al menos unas 19 esperas de ventana.

## `invalid_json`

La respuesta cruda recuperada fue:

```text
{"sentiment":"Neutro","confidence":0.99,"rationale":"El comentario solo describe una
```

Fue JSON truncado, no texto extra ni campo inesperado. Usage reportó exactamente 160 output tokens, igual al límite de `max_completion_tokens` del review experimental/productivo. La documentación actual de Cerebras confirma soporte de `response_format.type=json_schema` con `strict=true` para `gpt-oss-120b`; recomienda esa modalidad sobre `json_object`.

Propuesta experimental futura, no aplicada al runtime: schema estricto con `additionalProperties:false`, enum ternario, rationale más corto u opcional, persistencia de `finish_reason` y revisión del cap de salida. El schema reduce errores estructurales; también debe evitarse cortar una respuesta por límite de tokens.

## Textos cortos

Los 20 casos tienen hasta cuatro tokens, por lo que la regla `token_count <= 4` capturaría 20/20. Distribución real: 8 ES, 4 EN, 4 PT, 4 IT. Asumir español por defecto sería incorrecto en 12/20 (60%).

Accuracy del detector: 10/20 (50%): ES 50%, EN 25%, PT 50%, IT 75%. La política recomendada es `short_text_uncertain`: no asumir idioma, no traducir automáticamente y, si corresponde, revisar el original anonimizado.

## Decisión

B ofrece calidad comparable en respuestas válidas, mitad de llamadas, menor costo, menor latencia, misma minimización de privacidad y menos puntos de falla. En este set, la única desventaja observada fue un JSON truncado, también posible en A y abordable con contrato estructurado/cap adecuado.

Recomendación experimental: avanzar con B como candidata para textos EN/PT/IT y mantener A sólo como fallback o experimento comparativo. No cambiar runtime hasta validar schema estricto y una muestra mayor.
