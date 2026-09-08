# Neutrality research

Investigación aislada; no modifica inferencia ni artefactos productivos.

```powershell
python artifacts/experiments/neutrality_research/run_research.py
```

En otro checkout, las fuentes históricas pueden indicarse explícitamente:

```powershell
python artifacts/experiments/neutrality_research/run_research.py `
  --corpus C:\ruta\dataset_unificado.csv `
  --raw-synthetic C:\ruta\DB_amazon_multilingual_v6.csv
```

Entradas históricas de sólo lectura:

- `../_original_reference/data/processed/dataset_unificado.csv`
- `../_original_reference/data/raw/DB_amazon_multilingual_v6.csv`
- artefactos congelados en `models/`

Los benchmarks de 60 y 104 se reportan únicamente como diagnósticos ya observados. Las variantes fueron predeclaradas y no se selecciona ninguna sobre esos resultados.

Salidas:

- `corpus_audit.json`
- `experiment_metrics.json`
- `experiment_predictions.csv`
- `report.md`
