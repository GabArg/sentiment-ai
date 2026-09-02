# Privacidad y seguridad

## Qué puede salir de la app

- Direct review y traducción: sólo el comentario después de `anonymize_text`.
- Hybrid review: sólo el texto de análisis anonimizado; nunca expected ni confianza local.
- Informe IA: conteos, porcentajes y métricas agregadas minimizadas; no comentarios ni CSV.

La anonimización reemplaza emails, teléfonos, URLs e identificadores numéricos largos. Es reducción de riesgo, no garantía de desidentificación: nombres propios o contexto libre pueden permanecer.

## Qué no se envía

CSV completo, fila completa, columnas de negocio, region/channel/customer ID, expected labels, predicción/confianza local, API key y headers de autenticación. Los exports no incluyen texto anonimizado, raw responses ni analysis text generado.

## Activación y fallback

Todos los servicios externos son opt-in o requieren una acción explícita. Sin clave, timeout, 429, truncamiento, schema inválido o budget agotado, la clasificación continúa con fallback local y estado visible. `max_retries=0` en interacción/direct; batch mantiene política controlada.

## Auditoría RC1

Se revisaron archivos tracked y artefactos experimentales: no se hallaron claves, bearer tokens, `.env` ni `secrets.toml` versionados. El ejemplo contiene sólo un placeholder. `.streamlit/secrets.toml` está ignorado y no fue leído. Los headers persistibles usan allowlist y excluyen auth.
