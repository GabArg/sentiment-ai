# Fase 3.5B — Rate Limit Hardening

La documentación oficial de Cerebras describe un token bucket con reposición continua,
límites por tokens y requests, y doble control proyecto/organización. Los límites reales
pueden diferir por cuenta. Las respuestas documentan headers de tokens/minuto y
requests/día; los errores pueden exponer `Retry-After` y request ID mediante el SDK.

## Auditoría y cambio

El `RatePacer` anterior usaba reloj monotonic y una deque rolling, pero purgaba timestamps
al cumplir 60 segundos antes de considerar el margen de 0.25 s. Una reserva exactamente
en el borde podía salir sin protección. Ahora:

- la ventana efectiva es `60 + EXTERNAL_RATE_LIMIT_SAFETY_SECONDS`, default 62 s;
- check, espera, reevaluación y reserva ocurren dentro de un lock;
- después de cada sleep se vuelve a purgar y comprobar, sin asumir precisión perfecta;
- el timestamp se reserva antes de liberar el lock;
- traducción, hybrid y direct review siguen compartiendo el mismo coordinador;
- budget y pacing permanecen independientes;
- `max_retries=0` no cambió.

Los headers de error se filtran por allowlist: `Retry-After`, `x-request-id` y los headers
documentados de remaining/reset. Nunca se conservan auth headers.

## Validación real

15 requests, un proceso, sin concurrencia, tres grupos operativos de cinco:

- provider success 15/15;
- 0 HTTP 429, truncamientos o errores de schema;
- `finish_reason=stop` 15/15;
- pacing acumulado 115.781 s; wall-clock 129.440 s;
- inferencia min 766 ms, mediana 852 ms, max 1.553 ms;
- 4.200 input tokens, 1.047 output, 5.247 total;
- costo USD 0.00225525, promedio USD 0.00015035/request.

Gate 3.5B: **PASS**. No se combinan estas métricas operativas con el benchmark semántico
3.5. El gate semántico ya superaba calidad; esta prueba valida el hardening operacional.
La arquitectura queda apta para Fase 4 Consolidation, todavía sin declararse soporte
general production-ready.
