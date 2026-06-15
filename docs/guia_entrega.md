# Guia rapida de entrega

1. Ejecutar el dashboard y revisar que cargue en `http://127.0.0.1:8050`.
2. Si hace falta, descargar el GeoJSON con `python src/download_data.py`.
3. Generar graficos estaticos con `python src/make_static_charts.py`.
4. Generar el PDF final con `python src/generate_report.py`.
5. Opcional: ejecutar con Docker usando `docker build -t postes-kilometricos .` y `docker run --rm -p 8050:8050 postes-kilometricos`.
6. Subir el proyecto a un repositorio publico de GitHub.
7. Reemplazar en el PDF o en la portada del aula virtual el enlace de ejemplo por la URL real del repositorio.
8. Entregar `output/pdf/documentacion_postes_kilometricos.pdf` en el aula virtual.
