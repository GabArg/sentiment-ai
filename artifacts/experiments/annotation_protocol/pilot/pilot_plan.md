# Piloto humano de anotación — plan operativo

Estado: preparado, todavía sin datos ni anotadores asignados.

## Objetivos

- comprobar si dos personas aplican la guía de manera consistente;
- localizar definiciones ambiguas y subgrupos con desacuerdo;
- ensayar anonimización, paquetes ciegos, consolidación y adjudicación;
- validar `family_id` y separación de procedencias antes de construir development;
- medir carga operativa, no calidad del modelo.

## Tamaño y composición

Objetivo: 72 comentarios resolubles, dentro del rango 60–90. Agregar una reserva de 8–12 casos por posibles exclusiones, sin reemplazar casos después de observar acuerdo para mejorar artificialmente la métrica.

Muestreo planificado, no cuotas de etiqueta conocidas:

- 18 candidatos a hechos comerciales sin valoración;
- 12 opiniones explícitas positivas/negativas;
- 8 opiniones débiles;
- 8 opiniones mixtas o contrastes;
- 8 negaciones, incluidas polaridad inversora y doble negación;
- 6 problemas con resolución o elogio con problema;
- 6 textos cortos;
- 6 textos con varias oraciones/fuera de dominio.

La selección por subgrupo se realiza sin consultar predicciones ni etiquetas históricas. La distribución ternaria sólo se conoce después de adjudicar; no se reetiqueta para balancear.

## Criterios de entrada

- autorización/licencia y procedencia registradas;
- texto anonimizado y revisado;
- español comprendido por ambos anotadores para este primer piloto;
- al menos dos caracteres y contexto suficiente para intentar anotar;
- `case_id`, `source_id` y `family_id` opacos;
- ningún texto copiado de los benchmarks diagnósticos de 60/104;
- ninguna predicción o confidence calculada antes de cerrar etiquetas humanas.

## Asignación

1. Un coordinador forma el pool y congela texto/metadatos con hash.
2. Se generan dos paquetes idénticos A/B con una sola columna de etiqueta.
3. Los paquetes se entregan por separado y sin nombres de archivo que revelen a la otra persona.
4. Cada persona completa todos los casos en orden aleatorio distinto.
5. El coordinador calcula acuerdo sobre el solapamiento completo.
6. Todo desacuerdo y todo `Ambiguo` entra en adjudicación.

Antes de calcular métricas, `calculate_agreement.py` exige que ambos paquetes tengan exactamente los mismos `case_id` y que texto y metadatos compartidos coincidan para cada caso. El orden de las filas puede ser diferente. Cualquier ID faltante/adicional, duplicado o cambio estructural bloquea el cálculo; las etiquetas pueden diferir porque ese desacuerdo es el objeto de la medición.

## Éxito del piloto

El piloto no tiene un umbral automático de “aprobado”. La guía debe revisarse si ocurre cualquiera de estos casos:

- desacuerdo bruto superior al 20% global o superior al 30% en un subgrupo con al menos cinco casos;
- Cohen's kappa inferior a 0,60, interpretado junto con prevalencias y matriz de desacuerdo;
- tres o más desacuerdos con la misma causa conceptual;
- uso de `Ambiguo` o `No evaluable` superior al 15%;
- un anotador aplica sistemáticamente Neutro a opiniones mixtas;
- aparecen fallos de anonimización, familias mal agrupadas o contexto truncado;
- los anotadores solicitan información externa para decidir;
- la adjudicación revela que la guía permite dos decisiones igualmente defendibles.

Los valores son gatillos operativos para revisar el manual, no garantías estadísticas.

## Cierre

- Publicar acuerdo bruto, kappa, prevalencia por anotador y matriz completa.
- Documentar desacuerdos por motivo y subgrupo.
- Corregir la guía con versión nueva si cambia una decisión sustantiva.
- Repetir un mini-piloto nuevo con familias distintas después de cambios mayores.
- No incorporar el piloto a final; sólo podrá alimentar development si licencia, privacidad y calidad lo permiten y esa decisión se toma antes de evaluar modelos.
