# Postes kilométricos - Dashboard

Trabajo practico para Programacion Orientada al Analisis de Datos.

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

- `app.py`: aplicacion Dash que lee el GeoJSON crudo, arma un DataFrame y muestra filtros, KPIs, mapa y graficos Plotly.
- `src/download_data.py`: descarga el GeoJSON real.
- `src/make_static_charts.py`: crea los graficos requeridos con matplotlib y seaborn desde el GeoJSON crudo.
- `src/generate_report.py`: genera el PDF de documentacion.
- `Dockerfile`: permite ejecutar el dashboard dentro de un contenedor Docker.
- `data/raw`: GeoJSON original descargado.
- `assets`: estilos y graficos estaticos.
- `output/pdf`: documentacion final en PDF.
