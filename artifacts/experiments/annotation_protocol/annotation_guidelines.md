# Guía de anotación de sentimiento ternario

Versión de taxonomía: `sentiment-v1.0.0`
Alcance: sentimiento global expresado por el autor del comentario.
Unidad: un comentario completo, no palabras aisladas ni temas de negocio.

## Principio central

Lea el comentario completo y determine la evaluación global que comunica el autor. No infiera satisfacción a partir del evento descrito ni use una palabra como atajo. Si dos lecturas razonables conducen a clases distintas y el texto no permite resolverlas, marque `Ambiguo`; si no hay material lingüístico suficiente, marque `No evaluable`.

No consulte predicciones, probabilidades, reglas automáticas ni etiquetas de otra persona. No busque información externa para completar contexto ausente.

## Etiquetas

### Negativo

El autor expresa insatisfacción, perjuicio, rechazo, crítica, frustración o una evaluación desfavorable como conclusión dominante.

Indicadores válidos sólo dentro del contexto: valoración explícita, consecuencia perjudicial, intención de reclamar/devolver por disconformidad o contraste cuyo cierre es claramente desfavorable.

Ejemplo sintético de capacitación: “La instalación fue sencilla, pero desde ayer pierde datos y ya no puedo usarlo.” → `Negativo`.

### Neutro

El comentario informa, pregunta o describe sin una evaluación global positiva o negativa identificable. También puede describir un estado comercial sin valorar su conveniencia o consecuencia.

Ejemplo sintético: “La factura muestra dos artículos y fue emitida el 4 de marzo.” → `Neutro`.

Una frase factual no es automáticamente neutral. “La factura llegó tarde y por eso pagué un recargo” comunica una consecuencia desfavorable.

### Positivo

El autor expresa satisfacción, aprobación, alivio, recomendación o una evaluación favorable como conclusión dominante.

Ejemplo sintético: “El cambio quedó resuelto en el día y el nuevo equipo funciona perfectamente.” → `Positivo`.

### No evaluable

No hay evidencia suficiente para asignar sentimiento por problemas de forma o contenido: texto vacío, sólo identificadores, ruido ilegible, idioma fuera del alcance del lote, contenido truncado que pierde la evaluación o texto que no corresponde a feedback.

Ejemplos sintéticos: “---”; “PED-483920”; una secuencia corrupta imposible de interpretar.

No use `No evaluable` sólo porque el caso sea difícil.

### Ambiguo / requiere adjudicación

Existen al menos dos interpretaciones razonables con polaridades diferentes y el comentario no establece cuál domina. Registre el motivo; no fuerce Neutro.

Ejemplo sintético: “Llegó rápido. La calidad, bueno… ya veremos.” → `Ambiguo` por evaluación implícita insuficiente.

`Ambiguo` es una decisión de anotación intermedia. Un registro congelado debe quedar adjudicado a una clase ternaria o excluido como `No evaluable`.

## Regla de polaridad global

1. Identifique qué hechos se describen.
2. Separe hechos de evaluaciones explícitas o consecuencias valoradas.
3. Determine el alcance temporal: problema inicial, respuesta y estado final.
4. Observe conectores como “pero”, “aunque”, “sin embargo” y “al final”; no aplique una regla fija de “última cláusula gana”.
5. Pregunte qué evaluación global comunica el autor, no qué evento parece bueno o malo al anotador.
6. Si ninguna polaridad domina de manera defendible, marque `Ambiguo` y documente las lecturas.

## Casos frecuentes

### Hechos comerciales sin valoración

“El pedido figura en preparación desde las nueve.” → `Neutro` si sólo informa estado.
“El pedido sigue en preparación y ya perdí la fecha del evento.” → `Negativo` por consecuencia explícita.

### Opiniones explícitas

Priorice la evaluación explícita dentro del alcance global: “La atención fue excelente” → `Positivo`; “La atención fue decepcionante” → `Negativo`.

### Opiniones débiles

“Está bastante bien para uso ocasional” suele ser `Positivo` débil.
“Apenas cumple y no lo elegiría otra vez” es `Negativo` débil.
“Cumple” sin contexto puede ser `Neutro` o `Ambiguo`; no complete la intención.

La intensidad no cambia la clase; puede registrarse mediante `sentiment_subgroup`.

### Opiniones mixtas

No asigne Neutro automáticamente. Evalúe severidad, consecuencia y conclusión:

- “Es lindo, pero se apaga y no puedo trabajar” → `Negativo`.
- “La caja vino marcada, aunque el producto está perfecto y estoy conforme” → `Positivo`.
- “La pantalla es buena, la batería es mala y no sé si conservarlo” → `Ambiguo`.

### Negación simple

La palabra “no” no determina polaridad:

- “No funciona” → `Negativo`.
- “No tengo comentarios adicionales” → `Neutro`.
- “No tuve ningún inconveniente” → `Positivo` si comunica satisfacción; si sólo confirma ausencia de incidentes sin evaluación, documente la lectura y use `Ambiguo` cuando corresponda.

### Negación que invierte polaridad

Interprete la proposición completa:

- “No llegó tarde” describe ausencia de demora; puede ser neutral si no hay valoración.
- “No está nada mal” suele expresar aprobación débil → `Positivo`.
- “Sin problemas y más rápido de lo esperado” → `Positivo`.

### Doble negación

Resuelva el significado antes de etiquetar. “No puedo decir que no sirva” puede ser aprobación débil, reserva o evasión; sin más contexto corresponde `Ambiguo`.

### Contrastes

No suponga que la cláusula posterior siempre domina. Determine qué aspecto sostiene la conclusión y su impacto:

- “Tardó, pero llegó a tiempo para usarlo y quedé conforme” → `Positivo`.
- “La respuesta fue amable, pero nunca resolvieron el cobro” → `Negativo`.

### Ironía o sarcasmo

Etiquete sólo cuando las señales internas sean suficientes: “Excelente servicio: tres semanas sin respuesta” → `Negativo`. Si depende de tono no recuperable o conocimiento externo, `Ambiguo`.

### Textos cortos

“Excelente” → `Positivo`; “Pésimo” → `Negativo`; “Recibido” → `Neutro`; “Bueno…” → `Ambiguo` si la puntuación deja una lectura no resoluble.

### Varias oraciones

No etiquete por mayoría de oraciones. Considere el objeto principal, las consecuencias y la conclusión global. Si el comentario evalúa dos experiencias independientes con polaridades opuestas y ninguna domina, use `Ambiguo`.

### Problema con resolución positiva

Una queja resuelta no es siempre positiva:

- Resolución completa, valoración favorable y sin perjuicio persistente → normalmente `Positivo`.
- Resolución tardía con pérdida o insatisfacción persistente → `Negativo`.
- Sólo consta que fue resuelto, sin evaluación ni consecuencia → `Neutro`.

### Elogio con problema

Un elogio no neutraliza automáticamente un defecto. “Me encanta el diseño, pero llegó roto” → `Negativo` si el producto no puede utilizarse. “Funciona excelente; sólo preferiría otro color” → `Positivo`.

### Información insuficiente

Utilice solamente señales contenidas en el comentario y no reconstruya conversaciones o experiencias anteriores. Si una referencia ausente es necesaria para decidir entre polaridades razonables, marque `Ambiguo` y explique qué contexto falta.

- “Otra vez lo mismo” → `Ambiguo`: sugiere repetición, pero el comentario no permite saber qué ocurrió ni resolver por sí solo la polaridad global.
- “Como la vez anterior, volvieron a cobrarme de más” → `Negativo`: el comentario actual contiene una consecuencia desfavorable explícita; no hace falta conocer el episodio anterior.
- “Sí” o “No” sin la pregunta original → `No evaluable`: la unidad aislada no permite identificar ninguna evaluación.
- “Eso estuvo bien” → `Positivo`: aunque el referente no esté identificado, la valoración favorable está expresada en el comentario.

Reserve `No evaluable` para unidades que no permiten identificar ninguna evaluación sin su contexto original. No lo use cuando el comentario contiene dos o más lecturas de polaridad defendibles; esos casos corresponden a `Ambiguo`.

## Subgrupos permitidos

El subgrupo describe la construcción evaluada, no reemplaza la etiqueta: `factual`, `explicit_opinion`, `weak_opinion`, `mixed`, `simple_negation`, `polarity_inverting_negation`, `double_negation`, `contrast`, `sarcasm`, `short`, `multi_sentence`, `resolved_problem`, `praise_with_problem`, `out_of_domain`, `other`.

Seleccione el principal. Casos secundarios pueden documentarse en notas; ampliar a multietiqueta requiere una nueva versión del contrato.

## Registro de incertidumbre

Al usar `Ambiguo`, escriba dos lecturas concretas y por qué el texto no decide entre ellas. Al usar `No evaluable`, documente la condición objetiva que impide evaluar. No escriba “duda” sin explicación.

## Checklist antes de guardar

- Leí el comentario completo.
- No vi predicciones ni la etiqueta del otro anotador.
- Separé hechos, opiniones y consecuencias.
- No decidí por una keyword.
- Puedo justificar la polaridad global con evidencia textual.
- Si no puedo, usé `Ambiguo` o `No evaluable` con un motivo específico.
