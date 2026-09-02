# Índice de experimentos multilingües

Los artefactos permanecen en `artifacts/experiments/` y los runners en `scripts/` para no romper referencias versionadas.

| Fase | Pregunta | Resultado | Decisión |
|---|---|---|---|
| 3.0A | ¿Qué detector/arquitectura usar? | diseño privado y modular | avanzar por gates |
| 3.0B | ¿langdetect supera el gate? | 46/48; runtime OFF | integrar con fallback |
| 3.0C | ¿traducción funciona end-to-end? | traducción 6/6; local no mejoró | medir política |
| 3.1 | ¿negaciones y texto corto? | detector corto frágil; doble call costosa | comparar direct |
| 3.2 | ¿traducción o direct? | direct comparable, 1 call; un JSON truncado | estructurar contrato |
| 3.3 | ¿schema estricto basta? | forma estable; 128/192 insuficientes | probar 256 |
| 3.3B | ¿256 recupera fallos? | 5/5 | promover candidata |
| 3.4 | ¿integra runtime opt-in? | 8/8, sin fallos | validation gate |
| 3.5 | ¿calidad en 48 casos? | 47/48; provider 46/48 por 429 | endurecer pacing |
| 3.5B | ¿pacing evita 429? | 15/15 en tres ventanas | apta para consolidación |

Cada métrica pertenece a su muestra; no deben sumarse pruebas distintas como un benchmark único.
