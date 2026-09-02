# Arquitectura canónica v2

```text
texto validado
├─ <= 4 tokens
│  ├─ direct ON  → short_text_uncertain → review estructurado → final/fallback
│  └─ direct OFF → flujo configurado existente
├─ ES > 4
│  └─ modelo local → observabilidad → hybrid opcional → final/fallback
├─ EN/PT/IT > 4
│  ├─ direct ON  → original anonimizado → review estructurado → final/fallback
│  └─ direct OFF → flujo local o traducción legacy según configuración
└─ unsupported/error
   └─ fallback local/hybrid existente; nunca se inventa idioma
```

Soporte validado y todavía experimental: ES, EN, PT e IT. No se anuncia soporte universal.

## Flags y precedencia

| Flag | Default | Propósito | Dependencia/costo | Riesgo | Recomendación |
|---|---:|---|---|---|---|
| `ENABLE_DIRECT_MULTILINGUAL_REVIEW` | false | ruta canónica candidata para no-ES y textos breves | Cerebras, 1 call/caso | proveedor/RPM | preferida, opt-in |
| `ENABLE_HYBRID_SENTIMENT` | false | revisar incertidumbre local, principalmente ES | Cerebras según router | benchmark pequeño | mantener opt-in |
| `ENABLE_MULTILINGUAL_SENTIMENT` | false | detectar y traducir a ES antes de local | Cerebras, puede duplicar calls | costo/latencia | legacy experimental |
| informe IA | acción manual | segunda redacción ejecutiva | Cerebras por click | datos agregados/costo | separado de clasificación |

Direct tiene precedencia para sus casos y nunca se combina con traducción. Hybrid sigue disponible en la rama local española. La API key por sí sola no habilita flags.

## Configuración activa

| Variable | Default | Uso |
|---|---:|---|
| `CEREBRAS_API_KEY` | ausente | credencial server-side opcional |
| `HYBRID_THRESHOLD_NEGATIVE` | 0.80 | threshold experimental por clase |
| `HYBRID_THRESHOLD_NEUTRAL` | 0.65 | idem |
| `HYBRID_THRESHOLD_POSITIVE` | 0.80 | idem |
| `HYBRID_MAX_REVIEWS_PER_BATCH` | 25 | límite legacy de second checks |
| `HYBRID_MAX_EXTERNAL_CALLS_PER_BATCH` | 25 | budget conjunto recomendado |
| `HYBRID_MAX_REQUESTS` | 5 | capacidad rolling local |
| `HYBRID_WINDOW_SECONDS` | 60 | ventana base |
| `EXTERNAL_RATE_LIMIT_SAFETY_SECONDS` | 2.0 | margen preventivo |

Cuando multilingual está ON y no existe el budget global, `HYBRID_MAX_REVIEWS_PER_BATCH` actúa como alias compatible. Defaults sin clave/flags conservan operación local.
