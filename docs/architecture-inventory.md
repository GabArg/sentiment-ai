# Inventario de arquitectura v2

Clasificación: **A** productivo actual; **B** legacy/histórico funcional; **C** experimental/offline; **D** soporte; **E** obsoleto.

| Módulo | Propósito y consumidores principales | Flag | Clase | Decisión |
|---|---|---|---|---|
| `src/__init__.py` | paquete Python | — | D | mantener |
| `ai_provider.py` | informe ejecutivo Cerebras y fallback; `app`, tests | acción explícita | A | mantener |
| `analytics.py` | métricas y distribución; `app` | — | A | mantener |
| `batch.py` | local, hybrid, traducción y direct batch; `app` | los tres flags | A | mantener |
| `direct_multilingual.py` | routing directo y fallback; `app`, batch | direct | A | mantener |
| `direct_review_config.py` | config independiente de direct review | direct | A | mantener |
| `evaluation.py` | benchmark local offline | — | D | mantener |
| `external_requests.py` | budget y pacer global por operación | modos externos | A | mantener |
| `hybrid.py` | consolidación local/second check | hybrid | A | mantener |
| `hybrid_config.py` | thresholds, pacing y límites | hybrid/externo | A | mantener |
| `language_detection.py` | langdetect determinístico para textos largos | multilingual/direct | A | mantener |
| `model.py` | carga joblib e inferencia local | — | A | mantener |
| `multilingual_config.py` | traducción legacy y budget externo | multilingual | B | mantener/deprecar ruta |
| `multilingual_contracts.py` | contratos de idioma/traducción compartidos | multilingual/direct | A | mantener |
| `multilingual_pipeline.py` | detectar→traducir→local→hybrid | multilingual | B | mantener como legacy experimental |
| `pareto.py` | temas negativos y Pareto | — | A | mantener |
| `preprocessing.py` | CSV, texto y anonimización | — | A | mantener |
| `rate_pacer.py` | rolling window atómica y margen | modos externos | A | mantener |
| `reporting.py` | informe determinístico y contexto minimizado | — | A | mantener |
| `review_router.py` | routing auditable por confidence | hybrid | A | mantener |
| `router_evaluation.py` | exploración offline de estrategias | — | C | mantener como evidencia |
| `sentiment_review.py` | provider híbrido con rationale/confidence legacy | hybrid | A | mantener; no confundir con direct |
| `structured_sentiment_review.py` | provider direct estricto mínimo | direct | A | mantener canónico para no-español |
| `translation.py` | traducción estructurada a español | multilingual | B | mantener como legacy experimental |

No hay módulos clase E demostrados. La búsqueda de imports y la suite confirman consumidores; no se elimina código en RC1.
