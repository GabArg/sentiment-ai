# Protocolo humano de anotación de sentimiento

Infraestructura local y experimental para construir un dataset humano ternario. No contiene datos reales, nombres de anotadores, adjudicaciones ni predicciones. No modifica la aplicación ni llama servicios externos.

## Archivos

- `annotation_guidelines.md`: manual listo para capacitación y operación.
- `dataset_schema.json`: contrato versionado del dataset maestro.
- `annotation_template.csv`: paquete ciego para una persona.
- `adjudication_template.csv`: cabecera del maestro consolidado/cola de adjudicación.
- `label_changes_template.csv`: historial append-only de cambios posteriores.
- `validate_dataset.py`: validador estándar local, sin dependencias nuevas.
- `test_validator.py`: tests ejecutables del contrato.

Los templates sólo tienen cabeceras. Los ejemplos de la guía son sintéticos y sirven para capacitación; no son evidencia humana ni evaluación independiente.

## Flujo operativo

### 1. Ingesta y autorización

1. Registrar origen, licencia o autorización antes de copiar el texto.
2. Asignar un `source_id` opaco; no usar email, usuario, ticket o nombre como ID.
3. Mantener el dato original, si corresponde legalmente, fuera de este paquete y bajo acceso restringido.
4. Anonimizar antes de entregar a anotadores: emails, teléfonos, URLs, IDs largos y cualquier identificador contextual detectable.
5. La validación automática detecta patrones obvios, pero no garantiza desidentificación. Se requiere revisión humana de privacidad.

### 2. Duplicados y familias

1. Detectar duplicados byte a byte y tras normalización Unicode/espacios.
2. Revisar near-duplicates con una herramienta separada y registrar la decisión.
3. Asignar el mismo `family_id` a variantes, traducciones, paráfrasis, respuestas de una plantilla o comentarios del mismo hilo cuando compartan información.
4. Congelar `family_id` antes de asignar splits.
5. El validador rechaza una familia presente simultáneamente en `development` y `final`.

### 3. IDs y metadatos

- `case_id`: estable, único y sin significado personal.
- `source_id`: lote/procedencia, no persona.
- `family_id`: unidad de separación contra leakage.
- `source_type`: `authorized_feedback`, `public_dataset` o `synthetic`.
- `language`: BCP-47 reducido (`es`, `en`, `pt-BR`).
- `sentiment_subgroup`: construcción lingüística principal; no es una etiqueta de negocio.
- `created_at`: timestamp de incorporación en UTC, no fecha inventada del comentario.

### 4. Anotación independiente

El coordinador genera dos copias de `annotation_template.csv`. Cada copia contiene una única columna `annotator_label`. Nunca se distribuye el maestro ni una copia completada por la otra persona.

Los paquetes no incluyen:

- predicción o confidence del modelo;
- etiqueta histórica;
- etiqueta esperada de benchmark;
- decisión de otro anotador;
- temas o recomendaciones automáticas.

Cada persona lee `annotation_guidelines.md`, completa su etiqueta y usa `uncertainty_reason` para `Ambiguo` o `No evaluable`. Las notas deben señalar evidencia textual, no intuiciones sobre el modelo.

### 5. Consolidación y desacuerdos

Un coordinador une por `case_id`, sin transformar texto:

- etiquetas ternarias iguales → `annotation_status=annotated`;
- desacuerdo o al menos un `Ambiguo` → `annotation_status=disagreement`;
- dos `No evaluable` concordantes → `annotated`, candidato a exclusión antes de congelar;
- faltantes → permanece fuera de cualquier split evaluable.

`disagreement_reason` categoriza el conflicto: alcance global, negación, contraste, ironía, falta de contexto, error de lectura, guía insuficiente u otro documentado.

### 6. Adjudicación

La persona adjudicadora recibe texto, ambas etiquetas y razones, pero tampoco ve predicciones. Debe:

1. aplicar la misma versión de la guía;
2. elegir `Negativo`, `Neutro`, `Positivo` o `No evaluable`;
3. explicar evidencia y resolución en `adjudication_notes`;
4. proponer cambio de guía si el desacuerdo revela una laguna recurrente.

`Ambiguo` no es una etiqueta final. Si la evidencia sigue siendo insuficiente, el resultado final es `No evaluable` y el caso se excluye de métricas ternarias.

### 7. Control de calidad

Antes de congelar:

- validar esquema, IDs, timestamps, estados y ausencia de columnas del modelo;
- revisar el 100% de desacuerdos y no evaluables;
- auditar una muestra aleatoria de acuerdos por clase, fuente y subgrupo;
- revisar posibles PII de forma humana;
- verificar balance y cobertura, sin cambiar etiquetas para equilibrar;
- comprobar que ninguna familia cruce development/final;
- calcular acuerdo bruto y Cohen's kappa global y por subgrupo con las etiquetas independientes originales;
- publicar matriz de desacuerdos y prevalencias de cada anotador.

Cohen's kappa corrige parcialmente el acuerdo esperado por azar, pero depende de prevalencia y sesgo marginal; puede ser bajo con alto acuerdo en clases desbalanceadas o alto sin garantizar validez de la guía. No debe usarse solo ni calcularse después de reemplazar etiquetas por la adjudicación.

No se calculan métricas ficticias en este paquete.

### 8. Congelamiento

1. Resolver o excluir todos los casos.
2. Fijar la versión de taxonomía.
3. Crear manifests con SHA-256 de dataset, guía, esquema y log de cambios.
4. Marcar el snapshot como inmutable.
5. Guardar development accesible al equipo de experimentación.
6. Mantener final bajo un custodio que no participe en selección de alternativas.
7. Predeclarar métricas y criterios antes de abrir final.

### 9. Cambios posteriores

No sobrescribir silenciosamente una etiqueta congelada. Registrar cada modificación en `label_changes_template.csv` con estado/etiqueta anterior, nueva decisión, motivo, fecha, rol aprobador y versión de taxonomía. Un cambio material crea una nueva versión del dataset y nuevos hashes; las métricas previas conservan referencia al snapshot anterior.

## Uso del validador

Paquete ciego:

```powershell
python artifacts/experiments/annotation_protocol/validate_dataset.py `
  artifacts/experiments/annotation_protocol/annotation_template.csv --mode blind
```

Dataset maestro:

```powershell
python artifacts/experiments/annotation_protocol/validate_dataset.py `
  artifacts/experiments/annotation_protocol/adjudication_template.csv --mode master
```

Tests:

```powershell
python -m pytest -q artifacts/experiments/annotation_protocol/test_validator.py
```

## Estrategia de recolección

### Fuentes preferidas

1. Feedback real autorizado y anonimizado, muestreado por canal/dominio sin exportar atributos innecesarios.
2. Datasets públicos revisados caso por caso: antes de incorporar, verificar licencia, términos, redistribución, privacidad, idioma y compatibilidad con GPL. Este protocolo no afirma que una fuente concreta sea compatible.
3. Casos sintéticos sólo para capacitación, pruebas de contrato y cobertura provisional; siempre `source_type=synthetic`, `split=training_only`.

### Objetivos iniciales de planificación

- Piloto de guía: 60–90 casos fuera de evaluación, anotados por dos personas.
- Development humano: 450–600 casos resueltos, objetivo aproximado de 150–200 por clase.
- Final independiente: 300–450 casos resueltos, objetivo aproximado de 100–150 por clase.

Son tamaños operativos, no garantías de potencia estadística. Deben ajustarse según prevalencia, desacuerdo y análisis de intervalos de confianza. Conviene sobremuestrear candidatos neutrales factuales para obtener cobertura, pero las métricas de prevalencia real deben calcularse también sobre una muestra no balanceada representativa.

### Diversidad

- múltiples dominios comerciales y canales;
- redacción formal/informal y longitudes variadas;
- diferentes regiones de español, sólo cuando haya anotadores competentes;
- familias separadas entre splits;
- suficientes hechos, opiniones débiles, negaciones, contrastes y resoluciones;
- ninguna reutilización literal de los benchmarks diagnósticos de 60/104.

## Plan por etapas

1. Revisión de esta guía por producto, privacidad y dos futuros anotadores.
2. Piloto ciego de 60–90 casos; medir desacuerdos y revisar la guía, sin evaluar modelos.
3. Congelar `sentiment-v1.0.0` o publicar una versión corregida antes del dataset principal.
4. Recolectar y anotar development por familias.
5. Auditar calidad, acuerdo, balance y procedencia; congelar development.
6. Predeclarar alternativas y criterios de aceptación.
7. Recolectar final desde procedencia/familias no usadas en development y entregarlo a un custodio.
8. Experimentar sólo sobre development.
9. Abrir final una vez para la decisión predeclarada.
10. Si falla, no optimizar sobre final: volver a desarrollo y reservar un futuro snapshot independiente.

## Riesgos y criterios de aceptación

Riesgos: privacidad residual, licencia incompatible, anotadores no independientes, guía ambigua, prevalencia artificial, leakage por familia, cambios retroactivos, fatiga, sesgo regional y uso accidental de predicciones.

Aceptar un snapshot sólo si:

- autorización/licencia y procedencia están registradas;
- privacidad fue revisada más allá del regex;
- dos anotaciones independientes están completas;
- todos los desacuerdos fueron adjudicados o excluidos;
- acuerdo y matriz de desacuerdos están publicados con sus limitaciones;
- no hay duplicados/familias cruzadas;
- no existen columnas de predicción en paquetes humanos;
- las clases/subgrupos alcanzan la cobertura predeclarada;
- guía, esquema, dataset y cambios tienen versión y hash;
- final permaneció oculto durante selección;
- los casos sintéticos no se presentan como validación humana o independiente.
