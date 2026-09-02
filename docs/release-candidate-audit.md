# Auditoría v2.0.0-rc1

Fecha: 2026-09-02. Rama: `feature/v2-dashboard-ai-report`. Esta auditoría no autoriza merge ni activa flags.

## Arquitectura y módulos

La arquitectura canónica está en [architecture.md](architecture.md) y los 24 módulos en [architecture-inventory.md](architecture-inventory.md). Direct structured review es la ruta recomendada para EN/PT/IT y textos breves; español conserva local/hybrid. Traducción permanece legacy experimental. No se encontró código `src` demostrablemente obsoleto y no se eliminó runtime.

## Flags y configuración

Los tres flags son independientes y OFF por default. La matriz de ocho combinaciones pasa tests. La API key no habilita servicios. Thresholds, budget, RPM, ventana y safety margin están documentados y presentes en el ejemplo seguro. El informe IA continúa separado y por acción explícita.

## Tests y QA

- 214 tests; cobertura `src` 90%.
- `compileall`, `pip check`, `git diff --check`: OK.
- AppTest: local, hybrid, traducción legacy, direct, fallback, dashboard, report y labels humanos.
- Streamlit health: HTTP 200.
- Batch: orden, schema local/hybrid/multilingual/direct, budget compartido, pacing, export y ausencia de campos sensibles.
- No se hicieron llamadas reales en consolidación; se reutilizó la evidencia 3.5/3.5B.

La revisión final añadió CI para PR/main y corrigió dos HIGH antes de merge: trazabilidad batch tipada por contrato y privacidad direct-only correcta. Ambos tienen AppTest end-to-end, incluido CSV/download y fallback.

## Dependencias

| Dependencia | Uso | Decisión |
|---|---|---|
| Streamlit | UI/AppTest | mantener |
| scikit-learn | TF-IDF, modelo, métricas | mantener pin 1.8.0 |
| joblib | artefactos históricos | mantener |
| numpy | inferencia/evaluación | mantener |
| pandas | batch, fixtures, analytics | mantener |
| Plotly | charts | mantener |
| cerebras-cloud-sdk | report/reviews/traducción opt-in | mantener |
| langdetect | detector local | mantener pin 1.0.9 |
| pytest / pytest-cov | QA dev | mantener |

Python 3.12 confirmado. No hay dependencias runtime sin consumidor.

## Privacidad y seguridad

Auditoría completa en [privacy.md](privacy.md). No se detectaron credenciales, bearer tokens, `.env` ni secrets reales tracked. El único match fue el placeholder del ejemplo. Artefactos no contienen auth headers. Anonimización y minimización tienen tests; se documenta que no equivalen a desidentificación perfecta.

## Validación de calidad

- holdout histórico reconstruido: ~89.42%;
- benchmark local dirigido: 31/60;
- hybrid sobre el mismo benchmark: 59/60;
- validación multilingüe curada: 47/48, con un error de negación PT;
- hardening separado: 15/15 provider success, 0 HTTP 429.

No se combinan datasets ni se presentan como producción.

## Hallazgos por severidad

### BLOCKER

Ninguno.

### HIGH

Ninguno.

### MEDIUM

1. Validación multilingüe pequeña y curada; direct permanece opt-in.
2. El lock/pacer coordina un proceso, no múltiples workers o consumidores de la misma cuota organizacional.
3. Traducción legacy duplica superficie de mantenimiento; deprecar, medir uso y retirar en una versión posterior.

### LOW

1. Parsing de config repetido entre tres módulos; unificar sólo con migración testeada.
2. Runners experimentales permanecen planos en `scripts/`; se preservaron paths para reproducibilidad.
3. Modelo local conserva debilidad conocida en neutrales fuera de dominio.

## UI y deploy

Labels, tooltips, warnings, empty states, charts, uploads y fallbacks fueron recorridos por AppTest. El estado direct se humaniza sólo en tabla; CSV mantiene trazabilidad técnica. No se hizo redesign. Health local OK. Defaults despliegan local-only.

## Decisión

Con 0 BLOCKER, 0 HIGH, tests verdes, cobertura 90%, health OK y privacy audit limpio, la PR es **apta para pasar de Draft a Ready for Review**. Debe esperar aprobación explícita; no se cambió estado ni se hizo merge.
