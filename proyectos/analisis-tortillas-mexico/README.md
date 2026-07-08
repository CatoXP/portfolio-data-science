# Análisis Histórico y Predictivo del Precio de la Tortilla en México 🇲🇽🌽

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Pandas-2C2D72?style=for-the-badge&logo=pandas&logoColor=white"/>
  <img src="https://img.shields.io/badge/scikit_learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white"/>
  <img src="https://img.shields.io/badge/Jupyter-F37626.svg?&style=for-the-badge&logo=Jupyter&logoColor=white"/>
</p>

¡Bienvenido! Este es un proyecto de **Ciencia de Datos** enfocado en analizar uno de los elementos más importantes de la cultura y la vida diaria en México: **La Tortilla**. Con más de 300,000 registros históricos obtenidos del *Sistema Nacional de Información e Integración de Mercados*, nuestro objetivo es extraer verdadero valor a estos datos respondiendo preguntas cruciales e implementando *Machine Learning* predictivo.

## 🚀 Sobre este Proyecto

La tortilla no solo es gastronomía, es la base de la economía nutricional del país. Recientemente, su precio ha sufrido los azotes de la inflación moderna. El presente repositorio contiene un análisis de inicio a fin que abarca:

- **Data Wrangling**: Limpieza extensiva de datos, arreglando codificaciones incorrectas en strings, fechas y manejo de valores ausentes (*Missing Values*).
- **Análisis Exploratorio de Datos (EDA)**: Storytelling visual mostrando el doloroso incremento histórico del precio promedio.
- **Insite Comercial**: Comparativas de distribuciones (Violin Plots) del precio entre los gigantes **Retail** (como Walmart) versus pequeños comercios **"Mom and Pop stores"** (Tortillerías de barrio).
- **Proyecciones (Machine Learning)**: Desarrollo, entrenamiento y comparación entre **Regresión Lineal Simple** y **Bosques Aleatorios (Random Forest)** para descubrir el algoritmo ganador en la proyección de precios.

## 🗂️ Estructura del Repositorio

- `tortilla_prices.csv`: El conjunto de datos crudo (300k+ registros diarios con Ciudad, Estado, Año, Mes, Día y Precio Promedio).
- **`Analisis_Tortillas.ipynb`:** 🌟 ¡El núcleo del proyecto! Aquí yace el notebook principal detalladamente comentado y explicado paso a paso. Úsalo para reproducir mis hallazgos.

## 💡 Hallazgos Principales (Spoilers)

1. **La Paradoja Retail**: Sorprendentemente, los grandes minoristas venden más barato el Kilogramo que las tortillerías locales. (Las razones económicas asociadas a esto implican producción masiva e ingredientes mixtos).
2. **Inflación Lineal vs Factores Complejos**: Al aplicar machine learning, descubrimos que los comportamientos de subida de precio involucran interacciones altamente variables con los meses estacionales y la geografía. Aquí es donde **Random Forest** destroza las capacidades proyectivas de una mera Regresión Lineal.


