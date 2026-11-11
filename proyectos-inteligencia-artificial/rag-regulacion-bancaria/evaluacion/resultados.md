# Resultados de la evaluación

Evaluación del buscador (la etapa de *retrieval*) con 22 preguntas de prueba
escritas en lenguaje coloquial. Cada pregunta tiene uno o más artículos
esperados, verificados a mano contra el texto de la ley con `verificar.py`.

Fecha de la medición: 10 de noviembre de 2026.

## Métricas

- **Recall@5:** porcentaje de preguntas en las que un artículo esperado
  apareció entre los 5 resultados que recibe el LLM.
- **MRR (Mean Reciprocal Rank):** promedio de 1/posición del primer artículo
  correcto. Vale 1 si siempre sale en primer lugar y 0 si nunca aparece.

## Comparación de versiones

| Versión | Recall@5 | MRR | Decisión |
|---|---|---|---|
| `multilingual-e5-small` | 64% (14/22) | 0.37 | Línea base |
| `multilingual-e5-base` | 64% (14/22) | 0.47 | Mismo recall, mejor orden |
| **`multilingual-e5-base` + re-ranking** | **73% (16/22)** | **0.61** | **Versión final** |
| `multilingual-e5-base` + fusión RRF | 68% (15/22) | 0.55 | Descartada |

Dato adicional: con `multilingual-e5-base` sin re-ranking, el **Recall@20 es
de 91%** (20/22). Es decir, el artículo correcto casi siempre está entre los
20 candidatos; el problema principal era el orden, y por eso se agregó el
re-ranking.

Tiempo de indexado de los 799 chunks en CPU: 40 s con `e5-small` y
1 min 56 s con `e5-base`.

## Qué se probó y qué pasó

1. **Modelo de embeddings más grande.** No encontró más artículos, pero los
   ordenó mejor (MRR de 0.37 a 0.47). No fallan las mismas preguntas: el
   modelo grande perdió dos que el chico sí encontraba.
2. **Re-ranking con cross-encoder.** Se traen 20 candidatos y un segundo
   modelo los reordena. Rescató tres preguntas (artículos 65, 21 y 28) y
   rompió una que antes salía en primer lugar (46 Bis 1). Balance: +2.
3. **Fusión de rankings (RRF).** Se combinó el orden vectorial con el del
   cross-encoder. Recuperó el 46 Bis 1 pero perdió el 65 y el 28. Resultado
   peor que el re-ranking solo, así que se descartó.

## Detalle de la versión final

| # | Pregunta | Esperado | Resultado |
|---|---|---|---|
| 1 | ¿Qué operaciones puede realizar un banco? | 46 | Posición 1 |
| 2 | ¿Un banco puede dar información de mis cuentas a cualquiera? | 142 | Posición 1 |
| 3 | ¿Qué deben hacer los bancos para prevenir el lavado de dinero? | 115 | Posición 1 |
| 4 | ¿Quiénes pueden dar el servicio de banca en México? | 2o | Falla |
| 5 | ¿Quién da el permiso para abrir un banco nuevo? | 8o | Posición 2 |
| 6 | ¿Qué papeles hay que entregar para pedir autorización de un banco? | 10 | Falla |
| 7 | ¿Cuánto dinero necesita como mínimo un banco para operar? | 19 | Posición 1 |
| 8 | ¿Qué es un banco de desarrollo? | 30 | Posición 1 |
| 9 | ¿Un banco puede usar tiendas o terceros para atender a sus clientes? | 46 Bis 1 | Falla |
| 10 | ¿Cuánto capital debe mantener un banco frente a los riesgos que toma? | 50 | Posición 1 |
| 11 | ¿Qué debe revisar un banco antes de prestarle dinero a alguien? | 65 | Posición 2 |
| 12 | ¿Un banco puede prestarle dinero a sus propios dueños o directivos? | 73, 73 Bis | Falla |
| 13 | ¿Cualquier empresa puede recibir depósitos del público? | 103 | Posición 2 |
| 14 | ¿Qué cosas tiene prohibido hacer un banco? | 106 | Falla |
| 15 | ¿Qué multas le pueden poner a un banco que no cumple? | 108, 108 Bis | Posición 1 |
| 16 | ¿Qué pasa si alguien capta dinero del público sin autorización? | 111 | Falla |
| 17 | ¿Quién vigila a los bancos? | 117 | Posición 3 |
| 18 | ¿Quién dirige un banco? | 21 | Posición 1 |
| 19 | ¿Qué pasa con una cuenta que nadie ha movido en años? | 61 | Posición 1 |
| 20 | ¿Quién recibe el dinero de una cuenta si el titular muere? | 56 | Posición 1 |
| 21 | ¿Por qué razones le pueden quitar la autorización a un banco? | 28 | Posición 2 |
| 22 | ¿Qué pasa si un banco sale mal en su evaluación de desempeño? | 281 | Posición 1 |

## Limitaciones de esta evaluación

- **El conjunto es chico.** Con 22 preguntas, cada una vale 4.5 puntos de
  Recall. Diferencias de una pregunta entre versiones pueden ser casualidad.
- **Una pregunta no es independiente.** La pregunta 3 (lavado de dinero) se
  usó para diseñar el glosario del dominio, así que su acierto no cuenta como
  evidencia de generalización.
- **Solo se mide la búsqueda.** No se evalúa de forma automática la calidad
  de la respuesta que redacta el LLM.
