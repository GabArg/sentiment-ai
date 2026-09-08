# Especificación de benchmark de neutralidad

## Propósito

Evaluar sentimiento ternario fuera del corpus histórico, con énfasis en neutralidad factual, negación y contraste. Los benchmarks existentes de 60 y 104 casos permanecen como diagnóstico/regresión y no participan en decisiones de modelo, reglas o thresholds.

## Separación obligatoria

- **Development:** permite análisis de errores y comparación de alternativas.
- **Final congelado:** permanece oculto durante desarrollo y se abre una sola vez al alcanzar criterios predeclarados.
- Las familias de frases, entidades, productos y plantillas no pueden cruzar particiones.
- La separación debe hacerse por `family_id` y procedencia, nunca sólo por fila.

No existe todavía un conjunto final verdaderamente independiente. Su construcción y revisión humana quedan pendientes; no se inventa una cifra de generalización en esta fase.

## Esquema propuesto

| Campo | Uso |
|---|---|
| `case_id` | trazabilidad |
| `text` | única feature de sentimiento |
| `expected_sentiment` | referencia oculta al predictor |
| `subgroup` | evaluación estratificada |
| `family_id` | control de leakage semántico/templado |
| `source_type` | `human`, `production_sample` o `synthetic` |
| `language` | alcance lingüístico |
| `annotation_status` | revisión y adjudicación |

## Cobertura mínima por partición

Diseño equilibrado entre Negativo, Neutro y Positivo. Cada clase debe cubrir, cuando semánticamente corresponda:

- hechos sin valoración;
- opiniones fuertes y débiles;
- negación simple;
- negación que invierte polaridad (`sin problemas`, `no llegó tarde`);
- doble negación;
- contraste y cláusulas adversativas;
- lenguaje comercial de entrega, cobro, soporte, devolución y producto;
- textos cortos;
- varias oraciones;
- expresiones fuera del dominio histórico.

Una frase factual no se etiqueta automáticamente como neutral: puede contener una consecuencia valorativa explícita. Una frase con `no` tampoco se etiqueta automáticamente como negativa.

## Protocolo de anotación

1. Guía escrita con inclusiones, exclusiones y casos fronterizos.
2. Dos anotadores humanos independientes por caso.
3. Adjudicación de desacuerdos sin consultar predicciones.
4. Registro de acuerdo interanotador y motivos de ambigüedad.
5. Deduplicación exacta y revisión de similitud por `family_id` antes del split.
6. Los ejemplos sintéticos deben declarar `source_type=synthetic` y no compartir familias entre particiones.

## Criterios predeclarados antes de abrir final

- mejora de macro-F1 y recall neutral en development;
- ausencia de degradación material predefinida en Negativo y Positivo;
- reporte de errores de alta confianza;
- reproducibilidad con semillas y configuración versionadas;
- cobertura y abstención por clase si existe rechazo selectivo;
- revisión de privacidad y costo para cualquier componente no local.

El umbral numérico de mejora debe fijarse con el dueño del producto antes de consultar el conjunto final.
