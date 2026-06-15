from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "documentacion_postes_kilometricos.pdf"
RAW_DATA = ROOT / "data" / "raw" / "postes_1km_2018.geojson"
SCREENSHOT = ROOT / "screenshots" / "dashboard_postes_kilometricos.png"
MATPLOTLIB = ROOT / "assets" / "matplotlib_postes_distrito.png"
SEABORN = ROOT / "assets" / "seaborn_postes_ruta.png"
DATA_URL = (
    "https://ide.transporte.gob.ar/geoserver/observ/ows?service=WFS&version=1.0.0"
    "&request=GetFeature&typeName=observ:_3.4.1.1.4.poste_1km_2018"
    "&maxFeatures=28000&outputFormat=application%2Fjson"
)


def cargar_geojson() -> pd.DataFrame:
    with RAW_DATA.open(encoding="utf-8") as file:
        geojson = json.load(file)
    return pd.DataFrame([feature["properties"] for feature in geojson["features"]])


def stylesheet():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            parent=styles["Title"],
            fontSize=32,
            leading=36,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#18201f"),
            spaceAfter=18,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#106b5f"),
            spaceBefore=12,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["BodyText"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#444444"),
        )
    )
    return styles


def table(data, widths=None):
    t = Table(data, colWidths=widths, hAlign="LEFT")
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#106b5f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d8d0c1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f2e9")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return t


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#66716f"))
    canvas.drawString(1.6 * cm, 1.1 * cm, "Postes kilometricos - Dashboard")
    canvas.drawRightString(A4[0] - 1.6 * cm, 1.1 * cm, f"Pagina {doc.page}")
    canvas.restoreState()


def add_section(story, styles, title, body):
    story.append(Paragraph(title, styles["Section"]))
    for paragraph in body:
        story.append(Paragraph(paragraph, styles["BodyText"]))
        story.append(Spacer(1, 0.18 * cm))


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df = cargar_geojson()
    kpis = {
        "Postes": f"{len(df):,}".replace(",", "."),
        "Rutas": df["cod_ruta"].nunique(),
        "Distritos": df["distrito"].nunique(),
        "Progresiva maxima": int(df["progresiva"].max()),
        "Anio de ruta": int(df["ano_ruta"].mode().iloc[0]),
    }

    styles = stylesheet()
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        rightMargin=1.6 * cm,
        leftMargin=1.6 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.8 * cm,
    )
    story = []

    story.append(Spacer(1, 2.2 * cm))
    story.append(Paragraph("Postes kilometricos", styles["CoverTitle"]))
    story.append(Paragraph("Dashboard con GeoJSON real de IDE Transporte", styles["Title"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Programacion Orientada al Analisis de Datos - Examen Parcial Nro 1", styles["BodyText"]))
    story.append(Paragraph("Tecnicatura Superior en Ciencia de Datos e Inteligencia Artificial", styles["BodyText"]))
    story.append(Spacer(1, 0.8 * cm))
    story.append(
        table(
            [
                ["Campo", "Detalle"],
                ["Estudiantes", "Axel Fernandez"],
                ["Fecha de presentacion", "18/06/2026"],
                ["Repositorio", "Publicar en GitHub y reemplazar este texto por la URL real"],
            ],
            [5 * cm, 10 * cm],
        )
    )
    story.append(PageBreak())

    add_section(
        story,
        styles,
        "Proyecto",
        [
            "<b>Resumen ejecutivo.</b> El tablero permite explorar la distribucion de postes kilometricos de rutas argentinas publicados por IDE Transporte. Ayuda a identificar que rutas y distritos concentran mas registros y a ubicar visualmente los postes sobre un mapa.",
            "<b>Problema de negocio.</b> La informacion vial georreferenciada suele ser dificil de leer en formato GeoJSON. El dashboard transforma esa fuente en KPIs, filtros y graficos para consulta rapida.",
            "<b>Publico objetivo.</b> Estudiantes, analistas de datos, equipos de infraestructura vial y usuarios que necesitan inspeccionar registros de rutas por distrito, codigo de ruta y progresiva.",
            "<b>Herramientas.</b> Python, pandas, matplotlib, seaborn, plotly, Dash, reportlab, HTML/CSS y Git.",
        ],
    )
    story.append(table([["KPI", "Valor"]] + [[k, v] for k, v in kpis.items()], [5 * cm, 6 * cm]))

    add_section(
        story,
        styles,
        "Instalacion y ejecucion",
        [
            "Crear el entorno con <font name='Courier'>python3 -m venv .venv</font> y activarlo con <font name='Courier'>source .venv/bin/activate</font>.",
            "Instalar dependencias con <font name='Courier'>pip install -r requirements.txt</font>.",
            "Si hace falta volver a descargar la fuente, ejecutar <font name='Courier'>python src/download_data.py</font>.",
            "Generar los graficos estaticos con <font name='Courier'>python src/make_static_charts.py</font>.",
            "Levantar el dashboard con <font name='Courier'>python app.py</font> y abrir <font name='Courier'>http://127.0.0.1:8050</font>.",
            "Alternativa Docker: construir con <font name='Courier'>docker build -t postes-kilometricos .</font>, ejecutar con <font name='Courier'>docker run --rm -p 8050:8050 postes-kilometricos</font> y abrir <font name='Courier'>http://127.0.0.1:8050</font>.",
        ],
    )
    story.append(PageBreak())

    add_section(
        story,
        styles,
        "Documentacion tecnica",
        [
            "<b>Estructura.</b> La aplicacion esta en <font name='Courier'>app.py</font>. El GeoJSON crudo esta en <font name='Courier'>data/raw</font>. Los graficos estaticos estan en <font name='Courier'>assets</font>. La captura final esta en <font name='Courier'>screenshots</font>. El PDF final queda en <font name='Courier'>output/pdf</font>.",
            "<b>Uso del dataset.</b> No se genera un CSV limpio ni se altera la fuente original. El codigo lee el GeoJSON crudo, recorre <font name='Courier'>features</font>, toma <font name='Courier'>properties</font> y arma un DataFrame para contar, filtrar y graficar.",
            "<b>Interactividad.</b> Dash actualiza KPIs, mapa Plotly y graficos de barras cuando cambian los filtros de distrito, ruta y rango de progresiva.",
            "<b>Guia de estilo.</b> Tema operativo y sobrio. Paleta: tinta #18201f, fondo papel #f6f2e9, panel #fffdf8, verde #106b5f y acento rojo #d04f2f.",
        ],
    )
    story.append(Paragraph("Captura principal del dashboard: filtros, KPIs, mapa interactivo y graficos.", styles["Small"]))
    story.append(Image(str(SCREENSHOT), width=16.5 * cm, height=9.3 * cm))
    story.append(PageBreak())

    story.append(Paragraph("Graficos estaticos requeridos", styles["Section"]))
    story.append(Paragraph("Grafico generado con matplotlib desde el GeoJSON crudo.", styles["Small"]))
    story.append(Image(str(MATPLOTLIB), width=15.5 * cm, height=8.2 * cm))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Grafico generado con seaborn desde el GeoJSON crudo.", styles["Small"]))
    story.append(Image(str(SEABORN), width=15.5 * cm, height=8.2 * cm))
    story.append(PageBreak())

    dictionary = [
        ["Campo", "Descripcion"],
        ["id", "Identificador del registro en la fuente."],
        ["id_mojon", "Identificador del mojon o poste."],
        ["cod_ruta", "Codigo de ruta."],
        ["latitud / longitud", "Coordenadas geograficas del poste."],
        ["progresiva", "Kilometro o progresiva del poste."],
        ["ano_ruta", "Anio informado por la fuente para la ruta."],
        ["distancia", "Distancia registrada en la fuente."],
        ["desc", "Descripcion corta del poste."],
        ["distrito", "Distrito o jurisdiccion asociada."],
    ]
    add_section(
        story,
        styles,
        "Gobierno de datos",
        [
            f"<b>Fuente.</b> GeoJSON publico de IDE Transporte: <font name='Courier'>{DATA_URL}</font>.",
            "<b>Tuberia de datos.</b> El flujo es intencionalmente simple: descargar GeoJSON, leerlo con Python, convertir <font name='Courier'>properties</font> a DataFrame y usar pandas para conteos y filtros. No se imputan valores ni se eliminan registros.",
            "<b>Limitacion conocida.</b> Al no limpiar la fuente, cualquier valor faltante o inconsistente permanece tal como viene publicado. Esto se mantiene asi para respetar el dataset crudo pedido.",
        ],
    )
    story.append(table(dictionary, [4.4 * cm, 11.4 * cm]))
    story.append(PageBreak())

    add_section(
        story,
        styles,
        "Guia de usuario",
        [
            "<b>Glosario.</b> Poste: registro georreferenciado de un punto kilometrico. Ruta: codigo vial de la ruta. Distrito: jurisdiccion asociada. Progresiva: kilometro o avance sobre la ruta.",
            "<b>Navegacion.</b> Usar el filtro Distrito para ver una jurisdiccion especifica, Ruta para acotar por codigo de ruta y Rango de progresiva para limitar los kilometros mostrados. Los KPIs y graficos se recalculan automaticamente.",
            "<b>Mapa Plotly.</b> Cada punto representa un poste. Al pasar el mouse se ve distrito, codigo de ruta, progresiva y distancia. Si hay muchos puntos, la app muestra una muestra de hasta 5000 para mantener fluidez visual.",
            "<b>FAQ.</b> Si el tablero no abre, verificar que el entorno virtual este activo y que el puerto 8050 no este ocupado. Si faltan imagenes estaticas, ejecutar <font name='Courier'>python src/make_static_charts.py</font>. Si falta el GeoJSON, ejecutar <font name='Courier'>python src/download_data.py</font>.",
        ],
    )

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"PDF generado: {OUT}")


if __name__ == "__main__":
    main()
