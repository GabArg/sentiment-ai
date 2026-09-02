# ADR 001: direct multilingual structured review

- Estado: aceptado para release candidate, opt-in
- Fecha: 2026-09-02

## Contexto

La reconstrucción histórica detectaba idioma, traducía a español, clasificaba localmente y podía pedir otro review. Esto duplicaba llamadas y sumaba puntos de fallo sin mejorar sistemáticamente el clasificador local.

## Decisión

Para EN/PT/IT largos y textos de hasta cuatro tokens, preferir una única revisión multilingüe sobre el original anonimizado. Usar `gpt-oss-120b`, JSON Schema estricto con sólo `sentiment`, 256 completion tokens, fallback local y feature flag OFF por defecto. Mantener la traducción como ruta legacy durante RC1.

## Evidencia

- 3.2: direct redujo llamadas, costo y latencia frente a traducción+local+review.
- 3.3/3.3B: schema mínimo y 256 tokens eliminaron truncamientos en recuperación controlada.
- 3.4: integración 8/8.
- 3.5: 47/48 end-to-end en fixture curado; debilidad acotada en negación PT y 2 fallos operativos.
- 3.5B: pacing endurecido, 15/15 provider success y 0 HTTP 429.

## Consecuencias

Ventajas: una llamada, menor costo/latencia, menos estados intermedios, contrato auditable. Costos: dependencia externa para no-ES, límites de cuota, fallback local débil fuera de español y benchmark aún pequeño. No implica soporte universal ni production-ready general.
