# Credit Scoring Prediction — Give Me Some Credit

**Autor:** Brandon Uriel García Sánchez — Científico de Datos para Negocios · Finanzas / IA

**Dataset / Competencia:** [Kaggle - Give Me Some Credit](https://www.kaggle.com/competitions/GiveMeSomeCredit)

## Por qué este proyecto

Este es un proyecto de portafolio que resuelve un problema real de la industria financiera: *credit scoring*,
es decir, predecir la probabilidad de que un solicitante de crédito caiga en incumplimiento de pago grave
(90+ días de atraso) en los próximos 2 años. No es un dataset de juguete — es el tipo de modelo que un banco
real usa para decidir si otorga o no un préstamo.

El objetivo no fue solo entrenar un modelo, sino recorrer un pipeline completo de ciencia de datos con el
mismo rigor que se esperaría en un entorno bancario real: entender el negocio, diagnosticar problemas de
calidad de datos con evidencia (no suposiciones), tomar decisiones de limpieza justificadas, comparar modelos
con el criterio de negocio correcto (no solo accuracy), y explicar el modelo final de forma que sea
defendible ante un regulador.

## Problema de negocio

Los bancos deciden quién puede acceder a financiamiento y en qué condiciones — una decisión que puede definir
el éxito o fracaso de un solicitante y del propio banco. Los algoritmos de *credit scoring* estiman la
probabilidad de default de un solicitante para apoyar esa decisión de forma sistemática y justificable.

## Dataset

- `cs-training.csv` — set de entrenamiento (150,000 filas), incluye la variable objetivo `SeriousDlqin2yrs`.
- `cs-test.csv` — set de prueba oficial de Kaggle, sin la variable objetivo (no usado en este proyecto; se
  hizo un split propio de `cs-training.csv` para entrenar y evaluar).
- `Data Dictionary.xls` — diccionario de variables original.

Variable objetivo: `SeriousDlqin2yrs` — indica si la persona experimentó al menos un episodio de atraso de
pago de 90 días o más en los próximos 2 años (1 = sí, 0 = no).

## Metodología

### 1. Análisis Exploratorio de Datos (EDA)

Diagnóstico completo de calidad de datos, verificado con evidencia en cada paso (no supuestos):

- **Target desbalanceado:** 93.32% no cayó en default, 6.68% sí — esto descarta *accuracy* como métrica y
  define el uso de AUC-ROC y precision/recall desde el inicio.
- **`MonthlyIncome`:** ~20% de datos faltantes.
- **`DebtRatio`:** ~19.25% de las filas (28,877) con valores mayores a 10 (hasta 329,664). El 92.7% de esas
  filas coincide con `MonthlyIncome` faltante — un patrón sistemático ligado al ingreso, no errores
  aleatorios. Confirmado con correlación de Spearman (0.02): esta variable no aporta señal real en su
  estado corrupto.
- **`RevolvingUtilizationOfUnsecuredLines`:** solo 371 filas (0.25%) superan un valor de 2 — outlier aislado
  real. Con Spearman, esta variable sí tiene relación real con el target (0.24) — los outliers tapaban la
  señal con la correlación de Pearson (-0.00).
- **Columnas de días de atraso:** las tres comparten el mismo valor máximo (98 en 264 filas, 96 en 5 filas) —
  un código centinela, no conteos reales. Además están casi perfectamente correlacionadas entre sí
  (0.98-0.99).
- **`age = 0`** en 1 fila: error de captura aislado.

### 2. Preprocesamiento y Feature Engineering

- Split train/test (80/20, estratificado) **antes** de cualquier imputación o cálculo de estadísticas, para
  evitar fuga de datos (data leakage).
- Correcciones sin dependencia de datos (aplicadas antes del split): eliminación de la fila con `age = 0`,
  decodificación de códigos centinela (96/98) en las columnas de atraso, preservando la información en una
  bandera (`tiene_codigo_especial`).
- Imputación con mediana (ajustada solo con `train`) para `MonthlyIncome`, `NumberOfDependents` y las
  columnas de días de atraso.
- Capado de outliers: `RevolvingUtilizationOfUnsecuredLines` con percentil 99 de train (1.10);
  `DebtRatio` con límite fijo de dominio (3), ya que el percentil de train seguía corrupto por el mismo
  problema sistemático ligado al ingreso faltante.

### 3. Modelado

Se compararon dos modelos:

| Modelo | AUC-ROC | Accuracy | Precision (default) | Recall (default) |
|---|---|---|---|---|
| Regresión Logística | **0.861** | 0.81 | 0.22 | **0.75** |
| Random Forest | 0.838 | 0.93 | 0.53 | 0.16 |

**Se eligió Regresión Logística** como modelo final: aunque Random Forest tiene mayor accuracy, su recall en
la clase de default es mucho más bajo — se le escapa el 84% de los casos reales de default. Para un banco,
no detectar a alguien que sí va a caer en default (falso negativo) es más costoso que negarle el crédito a
alguien que sí hubiera pagado (falso positivo). La regresión logística también es más interpretable, un
requisito práctico en un contexto financiero regulado.

### 4. Explicabilidad (SHAP)

El análisis de SHAP confirmó, de forma independiente, los hallazgos del EDA:

- `RevolvingUtilizationOfUnsecuredLines` es la variable más influyente del modelo — consistente con su
  correlación de Spearman de 0.24.
- `DebtRatio` tiene un impacto mínimo — consistente con estar mayormente corrupta por el problema del
  ingreso faltante.
- Las variables de historial de atraso dominan el resto de la importancia, siguiendo un patrón ordinal
  (a mayor gravedad del atraso, mayor impacto en el riesgo).

## Comparación con el leaderboard de Kaggle

Como referencia orientativa (no una equivalencia exacta, ya que el AUC de este proyecto se calculó sobre un
test set propio y no sobre el test set oculto oficial de Kaggle): el primer lugar del leaderboard oficial de
esta competencia logró un AUC de 0.8696 con un ensamble complejo de varios modelos (925 participantes). Este
proyecto, con una sola regresión logística sin ensambles, logró un AUC de 0.861 — un resultado competitivo
para un modelo tan simple e interpretable.

## Limitaciones y siguientes pasos

- El modelo se entrenó con una sola partición train/test, sin validación cruzada.
- No se ajustó el umbral de decisión (0.5 por default) ni se probaron modelos más avanzados (XGBoost,
  ajuste de hiperparámetros) — el siguiente paso lógico para mejorar el recall sin sacrificar tanta
  precisión.
- `DebtRatio` sigue teniendo un problema de fondo sin resolver del todo más allá del capado; podría
  reconstruirse mejor con acceso a los datos originales de ingreso.

## Estructura del repositorio

```
├── Credit_Scoring_predicting.ipynb   # Notebook completo: EDA, preprocesamiento, modelado, evaluación, SHAP
├── cs-training.csv                   # Dataset de entrenamiento
├── cs-test.csv                       # Dataset de prueba oficial de Kaggle
├── sampleEntry.csv                   # Formato de entrega de Kaggle
├── Data Dictionary.xls               # Diccionario de variables
├── slides/                           # Resumen ejecutivo del proyecto en formato de presentación
└── README.md                         # Este archivo
```

## Cómo correr el proyecto

```bash
pip install pandas matplotlib seaborn numpy scikit-learn shap
jupyter notebook Credit_Scoring_predicting.ipynb
```

## Resumen en diapositivas

La carpeta [`slides/`](slides) contiene un resumen ejecutivo del proyecto en formato de presentación,
pensado para comunicar los hallazgos y la recomendación de negocio a una audiencia no técnica (por ejemplo,
un equipo de riesgo crediticio o dirección), sin necesidad de revisar el notebook completo:

1. **Portada** — presentación del proyecto y su objetivo.
2. **Mapa de correlación (heatmap)** — relación entre las variables del dataset y el target.
3. **Curva ROC** — desempeño del modelo final (AUC-ROC).
4. **Factores de riesgo** — variables con mayor influencia en la predicción, según SHAP.
5. **Caso de aplicación** — ejemplo de cómo se interpretaría el modelo en un caso real de decisión de crédito.
6. **Cierre y conclusiones** — resumen de resultados y siguientes pasos recomendados.
