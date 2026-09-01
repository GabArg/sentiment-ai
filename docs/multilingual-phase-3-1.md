# Fase 3.1 experimental: riesgos dirigidos

Esta fase no modifica el runtime. Evalúa español corto, negaciones multilingües y el costo operativo de traducir antes del second check.

## Fixture

`tests/fixtures/multilingual_risk_benchmark.csv` contiene 24 casos manuales y separados del benchmark anterior: 8 españoles cortos, 12 negaciones (4 EN, 4 PT, 4 IT) y 4 controles. Los expected labels no fueron generados por un LLM.

## Español corto

Langdetect acertó 3/8 (37,5%) en frases españolas de 2 a 4 palabras. Las ocho ejecuciones fueron estables en diez repeticiones por caso, pero cinco fueron errores estables: tres se clasificaron como portugués, una como italiano y una como catalán.

Los scores internos no detectaron incertidumbre: cuatro errores mostraron top score cercano a 0,99999 y el quinto 0,857. No deben usarse como confidence ni como gate de traducción.

La política recomendada para experimentar es considerar textos de hasta cuatro tokens como `short_text_uncertain` y no traducirlos automáticamente. Deben conservar el original y, si el modo híbrido está activo, permitir review multilingüe sobre el original anonimizado. Esta política es general y necesita un fixture corto no español para medir falsos positivos antes de implementarse.

## Negaciones: ejecución real

Se ejecutaron exactamente 12 traducciones reales y no se repitieron. El coordinador registró 12 traducciones y 15 reviews: nueve reviews derivados sobre traducción y seis comparaciones sobre original, promedio 2,25 llamadas por comentario.

La ejecución duró 303,9 segundos, incluidos 278,0 segundos de pacing. Latencia de traducción: mínimo 710 ms, mediana 861 ms, máximo 1.563 ms. Reviews sobre traducción: mínimo 800 ms, mediana 873 ms, máximo 1.753 ms. Reviews sobre original: mínimo 782 ms, mediana 935 ms, máximo 1.017 ms.

La salida estructurada de 513 líneas fue truncada por el canal de ejecución antes de persistir las doce filas completas. Para respetar el máximo explícito no se repitieron llamadas. Por ello no se publican accuracy, traducciones completas, tokens ni costos incompletos como si fueran resultados válidos. Se alcanzó a verificar un `invalid_json` en un review sobre traducción; su fallback funcionó.

El baseline reproducible sobre originales fue 2/12 (16,67%); el router actual derivaría 11/12 directamente sobre los originales. Esto hace técnicamente plausible evaluar review multilingüe directo, pero la comparación real de seis pares quedó incompleta por la pérdida de salida y no permite elegir aún entre traducción previa y review directo.

## Estrategias

| Estrategia | Llamadas observables/estimadas | Evidencia disponible | Estado |
|---|---:|---|---|
| A. Traducir todos | 12 traducciones + 9 reviews en esta corrida | Doble llamada frecuente | Costosa en 5 RPM |
| B. Original + hybrid | 11 reviews estimados por router local | Baseline original 2/12; comparación real incompleta | Candidata a validar |
| C. Traducir con confidence | No confiable para idioma; threshold local requiere evaluación | No hay accuracy completa recuperable | No elegir aún |
| D. Traducir por idioma | No hay evidencia recuperable por idioma suficiente | Fixture demasiado pequeño | No elegir |
| E. Traducción + local + hybrid | 21 llamadas para el flujo principal de 12 casos | Promedio principal 1,75 llamadas/caso | Operativamente lenta |

Con 5 RPM, una llamada por comentario requiere aproximadamente 2 ventanas para 12 casos; 21 llamadas requieren al menos 5 ventanas bajo pacing de ventana deslizante. La ejecución real completa, incluyendo seis comparaciones originales, usó 27 llamadas y tardó unos 5,1 minutos.

## Decisión

- Detector: no mantener langdetect sin política para texto corto. Probar un estado de incertidumbre por longitud, sin asumir español ni agregar reglas léxicas.
- Traducción: decisión pendiente. No hay evidencia válida suficiente para justificar que siga siendo central; el siguiente experimento debe comparar review directo sobre original contra review sobre traducción, persistiendo resultados localmente antes de imprimirlos y sin repetir esta corrida.
- Runtime: sin cambios en esta fase.
