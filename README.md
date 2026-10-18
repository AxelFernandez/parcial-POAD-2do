# Postes kilométricos - Dashboard

Trabajo práctico para Programación Orientada al Análisis de Datos. El dashboard
original se amplía con análisis descriptivo y una red neuronal sencilla para
comparar predicciones de distancia con una regla base.

## Dataset real

Se usa un GeoJSON publicado por IDE Transporte:

`https://ide.transporte.gob.ar/geoserver/observ/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=observ:_3.4.1.1.4.poste_1km_2018&maxFeatures=28000&outputFormat=application%2Fjson`

El dataset contiene postes de 1 km de rutas argentinas. Cada registro incluye codigo de ruta, distrito, latitud, longitud, progresiva, año de ruta y distancia. La app usa el GeoJSON crudo: solo parsea `features -> properties` para poder trabajar con pandas y graficar.

## Objetivo

Construir un dashboard simple para explorar donde estan los postes, que rutas tienen mas registros y en que distritos se concentran.

## Instalacion

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Descargar datos y generar graficos estaticos

```bash
python src/download_data.py
python src/make_static_charts.py
```

Para ejecutar el análisis estadístico y la evaluación de la red neuronal sin
abrir el dashboard:

```bash
python src/analysis.py
```

El modelo estima `distancia` con `progresiva`, `latitud` y `longitud`. Reserva
rutas completas para la evaluación, excluye distancias faltantes y compara una
red MLP de dos capas con una línea base que predice la mediana del conjunto de
entrenamiento. No usa IDs ni `desc`
como predictores porque son identificadores o duplican la progresiva. El
conjunto no permite pronosticar años futuros: todos los registros indican 2016.

## Ejecutar dashboard

```bash
python app.py
```

Luego abrir `http://127.0.0.1:8050`.

## Ejecutar con Docker

Construir la imagen:

```bash
docker build -t postes-kilometricos .
```

Ejecutar el contenedor:

```bash
docker run --rm -p 8050:8050 postes-kilometricos
```

Luego abrir `http://127.0.0.1:8050`.

## Estructura

- `app.py`: aplicación Dash con filtros, KPIs, mapa, gráficos Plotly y panel de resultados del modelo.
- `src/analysis.py`: carga y tipa datos con pandas, calcula descripciones y compara la red neuronal con la regla base.
- `src/download_data.py`: descarga el GeoJSON real.
- `src/make_static_charts.py`: crea los graficos requeridos con matplotlib y seaborn desde el GeoJSON crudo.
- `src/generate_report.py`: genera el PDF de documentacion.
- `Dockerfile`: permite ejecutar el dashboard dentro de un contenedor Docker.
- `data/raw`: GeoJSON original descargado.
- `assets`: estilos y graficos estaticos.
- `output/pdf`: documentacion final en PDF.

## Evaluación del modelo

La métrica principal es el error absoluto medio (MAE); también se informa la
raíz del error cuadrático medio (RMSE). Ambas se expresan en la escala de la
columna `distancia` publicada por la fuente. Los datos de
prueba pertenecen a rutas que no aparecen en entrenamiento. Es un ejercicio
académico con datos de una única fuente y un solo año, no una herramienta de
planificación vial ni un pronóstico operativo.

## Pruebas

```bash
python -m unittest discover -s tests -v
```
