# Investigación experimental de neutralidad factual

## Decisión ejecutiva

La debilidad neutral no se corrige con las normalizaciones mínimas evaluadas. En los benchmarks diagnósticos de 60 y 104 casos, la limpieza histórica y la normalización NFKC/espacios producen exactamente las mismas predicciones que el pipeline congelado. No existe evidencia suficiente para integrar reglas de factualidad ni elegir un threshold de abstención.

La siguiente inversión útil es construir un development set humano, equilibrado y separado por familias, y reservar un test final realmente independiente. Recién entonces corresponde comparar un modelo local alternativo o un detector de factualidad con abstención.

## Corpus histórico

| Medida | Resultado |
|---|---:|
| Filas procesadas | 25.188 |
| Positivo | 9.821 (39,0%) |
| Negativo | 9.507 (37,7%) |
| Neutro | 5.860 (23,3%) |
| Procedencia generador V6 | 16.812 (66,7%) |
| Amazon histórico | 5.243 |
| InterTASS 2017 | 3.033 |
| `datosjc` | 100 |

Los neutrales proceden principalmente del generador V6 (4.437); InterTASS aporta 1.011, Amazon histórico 378 y `datosjc` 34. La fuente Amazon tiene sólo 7,21% de neutrales, mientras el generador usa neutrales mixtos/valorativos creados por combinación de bloques. Esto deja poca representación clara de estados comerciales puramente factuales.

### Duplicación y calidad

- El raw V6 contiene 25.000 filas y 8.188 duplicados exactos.
- El corpus procesado no tiene duplicados exactos del texto crudo, pero aparecen 2.177 duplicados al aplicar la normalización histórica.
- Existe al menos un conflicto de etiqueta normalizado: `Igual que en la foto` figura como Positivo y `igual que en la foto` como Negativo.
- Al reconstruir el split aleatorio estratificado con `random_state=42`, 3.382 de 5.038 casos de test (67,13%) comparten con train al menos un segmento generado de cuatro o más palabras.

Compartir segmentos no prueba fuga directa de etiquetas, pero sí evidencia dependencia entre filas y hace que el holdout histórico de aproximadamente 89,42% sea una estimación in-domain potencialmente optimista. Un split futuro debe agrupar por fuente y familia textual.

## Entrenamiento y preprocessing

El entrenamiento histórico:

1. fusionó las fuentes y deduplicó por texto exacto antes de limpiar;
2. eliminó caracteres fuera de ASCII, vocales españolas acentuadas, `ñ`, dígitos, espacios y `.,!?`;
3. colapsó espacios, convirtió a minúsculas y aplicó `strip`;
4. realizó un split 80/20 estratificado por fila;
5. ajustó TF-IDF de 1–2 gramas, `min_df=3`, `max_df=0.9`, máximo 5.000 features;
6. seleccionó `C` y solver con CV de cinco folds optimizando accuracy;
7. entrenó LogisticRegression con `class_weight=balanced` y semilla 42.

Producción hoy sólo aplica `str + strip`; el vectorizador serializado hace lowercase y tokenización, pero no contiene el preprocessor histórico. La incompatibilidad aparece con guiones, símbolos, emojis y caracteres fuera del conjunto permitido: por ejemplo, el histórico concatena partes separadas por guión. Aplicarlo ahora cambiaría entradas existentes y requiere evaluación independiente.

## Coeficientes: evidencia e hipótesis

| Término | Peso Negativo | Peso Neutro | Peso Positivo |
|---|---:|---:|---:|
| compra | -0,300 | -1,510 | 1,811 |
| devolución | 1,553 | -0,855 | -0,698 |
| entrega | 0,368 | -0,939 | 0,570 |
| pedido | 0,336 | -0,349 | 0,012 |
| problema | 1,798 | -0,720 | -1,077 |
| producto | 0,437 | -0,835 | 0,398 |
| soporte | 0,295 | -0,024 | -0,271 |

`no` es la feature negativa de mayor peso (5,843). Entre las features positivas dominan `perfecto`, `genial`, `buena`, `excelente`, `calidad` y `compra`. Entre las neutrales aparecen `pero`, `precio`, `color`, `cumple` y construcciones mixtas.

Estos pesos son asociaciones condicionales del modelo lineal completo. Son compatibles con errores como `sin problemas`→Negativo, hechos con `producto/pedido`→Negativo y frases negativas con `compra`→Positivo, pero no demuestran causalidad de un término aislado.

## Comparación de preprocessing

Variantes predeclaradas:

- A: comportamiento actual `str + strip`;
- B: regex y normalización histórica;
- C: NFKC + colapso de espacios, sin eliminación léxica.

| Dataset diagnóstico | Variante | Accuracy | Macro-F1 | Recall neutral | Cambios de clase |
|---|---|---:|---:|---:|---:|
| Manual 60 | A actual | 0,5167 | 0,4868 | 0,2000 | 0 |
| Manual 60 | B histórico | 0,5167 | 0,4868 | 0,2000 | 0 |
| Manual 60 | C mínima | 0,5167 | 0,4868 | 0,2000 | 0 |
| Demo 104 | A actual | 0,7500 | 0,5198 | 0,0667 | 0 |
| Demo 104 | B histórico | 0,7500 | 0,5198 | 0,0667 | 0 |
| Demo 104 | C mínima | 0,7500 | 0,5198 | 0,0667 | 0 |

No se selecciona ninguna variante: ambos datasets ya fueron consultados durante diagnóstico. La igualdad sólo indica que sus textos no ejercitan suficientemente las incompatibilidades del preprocessing.

### Matrices del baseline

Orden de clases: Negativo, Neutro, Positivo.

Manual 60:

```text
[[11, 4,  5],
 [11, 4,  5],
 [ 3, 1, 16]]
```

Demo 104:

```text
[[66, 0,  8],
 [10, 1,  4],
 [ 3, 1, 11]]
```

## Factualidad y reglas

No se implementó un detector factual. El corpus contiene neutrales valorativos y mixtos, pocos neutrales comerciales factuales de fuente real y un conflicto de etiqueta demostrado. Una regla basada en fechas, pedidos o verbos descriptivos corregiría ejemplos conocidos, pero también podría neutralizar quejas factuales con consecuencias negativas. Keywords como `no`, `devolución` o `problema` tampoco representan polaridad por sí mismas.

Una alternativa futura requiere un development set anotado con subgrupos y una salida explícita `factual_score`/`abstain`, no un override silencioso de la clase.

## Abstención: sensibilidad, no selección

Se midieron thresholds redondos predeclarados sobre confidence local. No se optimizó ninguno.

| Dataset | Threshold | Cobertura | Accuracy cubierta | Macro-F1 cubierta | Errores cubiertos |
|---|---:|---:|---:|---:|---:|
| Manual 60 | 0,50 | 71,7% | 55,8% | 0,4748 | 19 |
| Manual 60 | 0,60 | 50,0% | 70,0% | 0,5976 | 9 |
| Manual 60 | 0,70 | 33,3% | 75,0% | 0,5357 | 5 |
| Manual 60 | 0,80 | 16,7% | 90,0% | 0,6410 | 1 |
| Demo 104 | 0,50 | 80,8% | 78,6% | 0,5090 | 18 |
| Demo 104 | 0,60 | 59,6% | 85,5% | 0,5647 | 9 |
| Demo 104 | 0,70 | 37,5% | 89,7% | 0,6028 | 4 |
| Demo 104 | 0,80 | 25,0% | 96,2% | 0,6325 | 1 |

La abstención es muy desigual: con 0,80 se abstiene en 95% de neutrales del benchmark 60 y 100% de neutrales del demo 104. La accuracy cubierta no es accuracy global y no justifica integrar ese threshold. Además permanece el error positivo de alta confianza sobre devolución/reintegro.

## Alternativas

| Alternativa | Evidencia actual | Beneficio posible | Riesgo/costo | Decisión |
|---|---|---|---|---|
| Baseline congelado | Completa y reproducible | Estabilidad | Neutral muy débil | Mantener como control |
| Preprocessing histórico | Sin cambios en 60/104 | Alineación con train | Cambia texto; evidencia insuficiente | No integrar |
| NFKC + espacios | Sin cambios en 60/104 | Robustez tipográfica | Beneficio no demostrado | No integrar |
| Reglas factuales | Corpus insuficiente | Interpretabilidad | Overrides frágiles/ad hoc | No implementar aún |
| Abstención | Mejora accuracy cubierta sacrificando cobertura | Reduce decisiones ambiguas | Rechaza casi todos los neutrales | Investigar con dev independiente |
| Modelo local alternativo | No evaluado | Mejor representación/clases | Datos, entrenamiento y mantenimiento | Sólo después del benchmark |

## Benchmark nuevo

La especificación completa está en `benchmark_spec.md`. Debe tener development y final congelado separados por `family_id` y procedencia, doble anotación humana, adjudicación y cobertura de neutralidad factual, opiniones débiles, negación inversora, doble negación, contrastes, comercio, textos cortos/largos y fuera de dominio.

No se creó un test final sintético: no sería validación independiente. Los 60 y 104 permanecen como regresión descriptiva.

## Recomendación y plan

1. Crear guía de anotación ternaria con casos frontera y política de ambigüedad.
2. Recolectar un development set humano equilibrado y agrupado por familia/fuente.
3. Mantener oculto un final set independiente, idealmente con feedback real anonimizado y consentimiento adecuado.
4. Fijar antes de abrir final los mínimos de macro-F1, recall neutral, degradación permitida por clase, cobertura y errores de alta confianza.
5. Comparar en development: baseline, preprocessing, abstención y un clasificador local alternativo con artefactos separados.
6. Considerar detector factual sólo si supera reglas simples sin degradar opiniones débiles o hechos con consecuencias.
7. Abrir final una sola vez; si falla, volver a desarrollo con un nuevo final futuro, no iterar sobre el mismo.

## Criterios de aceptación propuestos

- mejora reproducible de macro-F1 y recall neutral en development y final;
- ningún descenso material preacordado en recall Negativo/Positivo;
- matrices y métricas por subgrupo, no sólo accuracy;
- cero leakage por texto, normalización o familia;
- errores de alta confianza explícitos;
- si hay abstención: cobertura global, por clase y por subgrupo;
- artefactos, seeds, dependencias y hashes versionados por experimento;
- inferencia local y privacidad equivalentes o riesgo adicional documentado;
- rollback inmediato al modelo congelado;
- revisión humana de etiquetas ambiguas.

## Limitaciones

- El corpus original combina datos sintéticos, reviews y tweets con dominios distintos.
- La procedencia disponible no incluye una auditoría humana completa de etiquetas.
- La heurística de segmentos compartidos aproxima familias; no es un detector semántico exhaustivo.
- Los coeficientes no son explicaciones causales.
- Los benchmarks diagnósticos ya fueron observados y no sirven para selección.
- No existe aún evaluación final independiente.
