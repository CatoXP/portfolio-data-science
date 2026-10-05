<p align="center"><a href="https://github.com/CatoXP"><img src="https://raw.githubusercontent.com/CatoXP/CatoXP/main/assets/banner_es.svg" width="100%" alt="Brandon Uriel García Sánchez — Científico de Datos para Negocios"></a></p>

# Portafolio de Ciencia de Datos

**Proyectos de ciencia de datos aplicada a negocio, finanzas e IA** · Brandon Uriel García Sánchez

[![Perfil](https://img.shields.io/badge/GitHub-CatoXP-17171a?style=flat-square&logo=github&logoColor=ff2e3a)](https://github.com/CatoXP)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Brandon_Uriel_García_Sánchez-ff2e3a?style=flat-square&logo=linkedin&logoColor=0a0a0b)](https://www.linkedin.com/in/brandon-uriel-garcia-sanchez-9ab77b320/)
[![Arcade](https://img.shields.io/badge/Portafolio_web-arcade-f2ede3?style=flat-square&logo=githubpages&logoColor=0a0a0b)](https://catoxp.github.io/portafolio-datascience-arcade/)

Estudiante de Ciencias de Datos para Negocios (UNRC) y becario de Desarrollo y Automatización en HSBC GSC.
Cada proyecto tiene su carpeta con notebook, README propio y una **presentación** con la misma identidad visual.

## Proyectos

| # | Proyecto | Qué resuelve | Resultado | Stack | Slides |
|---|---|---|---|---|---|
| 01 | [💳 Credit Scoring Prediction](proyectos/credit-scoring-predicting) | Riesgo de impago a 2 años (Kaggle · Give Me Some Credit), con explicabilidad SHAP | **AUC 0.861** · detecta 75 de cada 100 morosos | Python · scikit-learn · SHAP | [PDF](proyectos/credit-scoring-predicting/slides/credit_scoring_deck.pdf) |
| 02 | [🏆 Home Credit Default Risk — GCI World 2026](proyectos/home-credit-default-risk-gci-utokyo) | Competencia de ML del Matsuo-Iwasawa Lab, The University of Tokyo | **Top 16** público · AUC 0.774 | LightGBM · XGBoost · CatBoost | [PDF](proyectos/home-credit-default-risk-gci-utokyo/slides/home_credit_deck.pdf) |
| 03 | [🛒 Hábitos de consumo en retail digital](proyectos/analisis-predictivo-consumo-retail) | SQL, reglas de asociación y dashboard para una tienda en línea | €39.9M analizados · −82% detectado ene→dic | SQL · Python · Power BI | [PDF](proyectos/analisis-predictivo-consumo-retail/slides/retail_deck.pdf) |
| 04 | [🌽 Precio de la tortilla en México](proyectos/analisis-tortillas-mexico) | EDA y predicción con 294k registros del SNIIM | **R² 0.962** · error medio $0.65/kg | pandas · scikit-learn · Plotly | [PDF](proyectos/analisis-tortillas-mexico/slides/tortillas_deck.pdf) |
| 05 | [🚇 Robos en el Metro de la CDMX](proyectos/analisis-robos-metro-cdmx) | Datos abiertos de la Fiscalía: cuándo, dónde y pronóstico 2025 | 56% de los robos en la mañana | Python · scikit-learn · Power BI | [PDF](proyectos/analisis-robos-metro-cdmx/slides/metro_cdmx_deck.pdf) |
| 06 | [🧺 Market Basket Analysis](proyectos/market-basket-consumo) | Reglas de asociación implementadas desde cero | 399 reglas · lift máx. 3.6x | Python · pandas · SQLite | [PDF](proyectos/market-basket-consumo/slides/market_basket_deck.pdf) |
| 07 | [🎬 Traductor de subtítulos en vivo](proyectos/traductor-subtitulos-live) | OCR + traducción offline inglés → español sobre cualquier video | ~226 ms por línea · OCR 11x más rápido | RapidOCR · Argos · Tkinter | [PDF](proyectos/traductor-subtitulos-live/slides/traductor_deck.pdf) |
| 08 | [🌍 Esperanza de vida en el mundo](proyectos/analisis-esperanza-vida) | Estadística descriptiva de 142 países, 1952–2007 | +17.9 años · brecha de 43 años | pandas · seaborn | [PDF](proyectos/analisis-esperanza-vida/slides/esperanza_vida_deck.pdf) |

## Otros proyectos (repositorios independientes)

| Proyecto | Qué es | Enlaces |
|---|---|---|
| 🐄 Detección de patologías bovinas | Dataset propio de 391 imágenes, YOLOv8 + termografía infrarroja | [Repo](https://github.com/CatoXP/deteccion-bovinos-cnn) |
| 🌴 Torre del Caribe | Proyecto en equipo (responsable técnico): campaña de turismo con datos para el sur de Quintana Roo, 8.1M registros | [Sitio](https://catoxp.github.io/torre-del-caribe-unrc-2026/) · [Repo](https://github.com/CatoXP/torre-del-caribe-unrc-2026) |
| 🎓 Deserción escolar | EDA de la deserción escolar en México y la UNRC con SQL | [Repo](https://github.com/CatoXP/desercion-escolar-eda) |
| 💊 Medicamentos en Iztapalapa | Proyección del consumo de medicamentos y simulación de control de calidad | [Repo](https://github.com/CatoXP/Simulacion-y-Proyeccion-de-Medicamentos-en-Iztapalapa-usando-Ciencia-de-Datos) |
| 🏥 Sistema de citas médicas | Reserva de citas en línea para el Centro de Salud Rafael Carrillo | [Sitio](https://catoxp.github.io/centro-de-salud-rafael-carrillo-sistema-citas/) · [Repo](https://github.com/CatoXP/centro-de-salud-rafael-carrillo-sistema-citas) |

## Cómo está organizado

```
portfolio-data-science/
├── proyectos/<proyecto>/     un proyecto terminado: notebook, datos (cuando se pueden compartir), README y slides/
│   └── slides/               presentación (PDF + PPTX), vista previa y gráficas
└── scripts/                  ejercicios de curso, prácticas y apuntes (no son proyectos terminados)
```

Cómo trabajo cada proyecto: valido antes de confiar en un número (validación cruzada, sin fuga de datos), documento
también lo que no funcionó y cierro con una conclusión de negocio en una frase.

---
<sub>Identidad visual compartida con mi [perfil de GitHub](https://github.com/CatoXP) y mi [portafolio web](https://catoxp.github.io/portafolio-datascience-arcade/).</sub>
