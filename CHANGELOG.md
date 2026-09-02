# Changelog

## [2.0.0-rc1] - 2026-09-02

### Added

- recuperación segura de los artefactos históricos TF-IDF + LogisticRegression;
- dashboard, batch, Pareto, informes determinístico/IA y exports;
- hybrid second check opt-in con routing por clase y fallback;
- direct multilingual structured review opt-in para ES/EN/PT/IT;
- anonimización, budget externo global, pacing rolling atómico y observabilidad;
- benchmarks versionados, artefactos auditables y más de 200 tests.

### Changed

- direct review reemplaza conceptualmente traducción→local→review como ruta multilingüe recomendada;
- traducción se conserva como legacy experimental;
- README y documentación reflejan la arquitectura v2 actual.

### Fixed

- trazabilidad batch direct deja de reutilizar un summary híbrido incompatible;
- privacidad de la página Acerca del proyecto contempla direct review en todas las combinaciones de flags;
- CI valida tests, cobertura, compilación y dependencias sin secrets.

### Security

- servicios externos OFF por defecto;
- contexto externo minimizado y sin credenciales en logs/artefactos;
- fallback explícito ante key ausente, timeout, 429, truncamiento o schema inválido.

No se creó tag ni release para esta candidata.
