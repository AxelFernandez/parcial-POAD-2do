"""Genera la documentación del segundo parcial en PDF."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.analysis import analyze_data, load_data


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "documentacion_postes_kilometricos_parcial2.pdf"
SCREENSHOT_OVERVIEW = ROOT / "screenshots" / "dashboard_overview_annotated.png"
SCREENSHOT_CHARTS = ROOT / "screenshots" / "dashboard_charts_annotated.png"
SCREENSHOT_ANALYSIS = ROOT / "screenshots" / "dashboard_analysis_annotated.png"
DATA_URL = (
    "https://ide.transporte.gob.ar/geoserver/observ/ows?service=WFS&version=1.0.0"
    "&request=GetFeature&typeName=observ:_3.4.1.1.4.poste_1km_2018"
    "&maxFeatures=28000&outputFormat=application%2Fjson"
)
DATA_URL_HTML = DATA_URL.replace("&", "&amp;")
REPOSITORY_URL = "https://github.com/AxelFernandez/parcial-POAD-2do/tree/codex/poad-parcial2-analisis"
INK = colors.HexColor("#18201f")
MUTED = colors.HexColor("#66716f")
PAPER = colors.HexColor("#f6f2e9")
PANEL = colors.HexColor("#fffdf8")
GREEN = colors.HexColor("#106b5f")
RED = colors.HexColor("#d04f2f")
LINE = colors.HexColor("#d8d0c1")


def fmt_int(value: int | float) -> str:
    return f"{int(value):,}".replace(",", ".")


def fmt_decimal(value: int | float) -> str:
    return f"{value:.2f}".replace(".", ",")


def fmt_one(value: int | float) -> str:
    return f"{value:.1f}".replace(".", ",")


def stylesheet():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=30,
            leading=35,
            alignment=TA_CENTER,
            textColor=INK,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CoverSubtitle",
            parent=styles["BodyText"],
            fontSize=13,
            leading=18,
            alignment=TA_CENTER,
            textColor=MUTED,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=23,
            textColor=GREEN,
            spaceBefore=4,
            spaceAfter=9,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Subsection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=INK,
            spaceBefore=8,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["BodyText"],
            fontSize=9,
            leading=13,
            textColor=INK,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallText",
            parent=styles["BodyText"],
            fontSize=7.7,
            leading=10,
            textColor=MUTED,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableHeader",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Callout",
            parent=styles["BodyText"],
            fontSize=8.5,
            leading=11,
            textColor=INK,
        )
    )
    return styles


def table(rows, widths, styles, header=True):
    body_style = styles["SmallText"]
    converted = []
    for row_index, row in enumerate(rows):
        cell_style = styles["TableHeader"] if header and row_index == 0 else body_style
        converted.append([Paragraph(str(value), cell_style) for value in row])

    result = Table(converted, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [colors.white, PAPER]),
    ]
    if header:
        commands.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), GREEN),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ]
        )
    result.setStyle(TableStyle(commands))
    return result


def add_section(story, styles, title, paragraphs):
    story.append(Paragraph(title, styles["Section"]))
    for text in paragraphs:
        story.append(Paragraph(text, styles["Body"]))


def pipeline_diagram() -> Drawing:
    drawing = Drawing(500, 80)
    labels = [
        ("GeoJSON", "IDE Transporte"),
        ("pandas", "tipos y control"),
        ("Descriptivos", "filtros y gráficos"),
        ("Rutas separadas", "MLP y métricas"),
    ]
    box_width = 105
    starts = [6, 132, 258, 384]
    for index, (x, label) in enumerate(zip(starts, labels)):
        drawing.add(Rect(x, 13, box_width, 52, rx=6, ry=6, fillColor=PANEL, strokeColor=LINE, strokeWidth=1))
        drawing.add(String(x + 8, 43, label[0], fontName="Helvetica-Bold", fontSize=9, fillColor=GREEN))
        drawing.add(String(x + 8, 28, label[1], fontName="Helvetica", fontSize=7.5, fillColor=INK))
        if index < len(starts) - 1:
            arrow_start = x + box_width + 3
            arrow_end = starts[index + 1] - 3
            drawing.add(Line(arrow_start, 39, arrow_end - 7, 39, strokeColor=RED, strokeWidth=1.4))
            drawing.add(
                Polygon(
                    [arrow_end - 9, 43, arrow_end - 1, 39, arrow_end - 9, 35],
                    fillColor=RED,
                    strokeColor=RED,
                )
            )
    return drawing


def fitted_image(path: Path, width_cm: float = 16.8):
    image = Image(str(path))
    # Load intrinsic dimensions first: with ReportLab's lazy PNG reader,
    # accessing imageWidth/imageHeight after assigning drawWidth resets it
    # to the image's pixel width and makes the screenshot overflow the page.
    image_width = image.imageWidth
    image_height = image.imageHeight
    image.drawWidth = width_cm * cm
    image.drawHeight = image.drawWidth * image_height / image_width
    return image


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.6)
    canvas.line(1.6 * cm, 1.45 * cm, A4[0] - 1.6 * cm, 1.45 * cm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(1.6 * cm, 1.08 * cm, "Postes kilométricos | POAD | Parcial 2")
    canvas.drawRightString(A4[0] - 1.6 * cm, 1.08 * cm, f"Página {doc.page}")
    canvas.restoreState()


def quality_counts(data: pd.DataFrame) -> dict[str, int]:
    lat_ok = data["latitud"].between(-90, 90)
    lon_ok = data["longitud"].between(-180, 180)
    progress_ok = data["progresiva"].ge(0)
    id_duplicates = int(data["id"].duplicated().sum())
    desc_matches = int(data["desc"].astype(str).eq(data["progresiva"].astype("Int64").astype(str)).sum())
    return {
        "coordinates_out_of_range": int((~lat_ok | ~lon_ok).sum()),
        "negative_progressiva": int((~progress_ok).sum()),
        "duplicate_id": id_duplicates,
        "desc_equals_progressiva": desc_matches,
        "missing_distance": int(data["distancia"].isna().sum()),
    }


def main() -> None:
    data = load_data()
    result = analyze_data(data)
    summary = result["summary"]
    model = result["model"]
    quality = quality_counts(data)
    styles = stylesheet()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        rightMargin=1.6 * cm,
        leftMargin=1.6 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.8 * cm,
        title="Postes kilométricos - Examen Parcial 2",
        author="Axel Fernández",
        subject="Dashboard con análisis estadístico y red neuronal",
    )
    story = []

    cover_band = Table([[""]], colWidths=[17.8 * cm], rowHeights=[0.36 * cm])
    cover_band.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), GREEN)]))
    story.append(Spacer(1, 1.7 * cm))
    story.append(cover_band)
    story.append(Spacer(1, 1.0 * cm))
    story.append(Paragraph("INSTITUTO SUPERIOR MANUEL BELGRANO", styles["SmallText"]))
    story.append(Spacer(1, 0.45 * cm))
    story.append(Paragraph("Postes kilométricos", styles["CoverTitle"]))
    story.append(Paragraph("Dashboard de análisis de datos con GeoJSON real", styles["CoverSubtitle"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Examen Parcial N° 2 | Programación Orientada al Análisis de Datos", styles["CoverSubtitle"]))
    story.append(Spacer(1, 1.0 * cm))
    story.append(
        table(
            [
                ["Dato", "Detalle"],
                ["Carrera", "Tecnicatura Superior en Ciencia de Datos e Inteligencia Artificial"],
                ["Curso y sede", "2do 4 | Godoy Cruz"],
                ["Docente", "Juan Caballero Gallar | Ciclo Lectivo 2026"],
                ["Estudiante", "Axel Fernández"],
                ["Fecha de entrega", "30/10/2026 - Aula Virtual"],
                ["Fecha de preparación", "17/10/2026"],
            ],
            [4.3 * cm, 13.5 * cm],
            styles,
        )
    )
    story.append(Spacer(1, 0.6 * cm))
    story.append(
        Paragraph(
            "Rama de esta entrega: <font name='Courier'>codex/poad-parcial2-analisis</font> del repositorio público.",
            styles["SmallText"],
        )
    )
    story.append(PageBreak())

    add_section(
        story,
        styles,
        "1. Proyecto",
        [
            "<b>Resumen ejecutivo.</b> El proyecto amplía el dashboard del primer parcial para explorar postes kilométricos publicados por IDE Transporte. Permite filtrar registros por distrito, ruta y progresiva, consultar su distribución y comparar una red neuronal con una línea base simple para estimar el campo <font name='Courier'>distancia</font>.",
            "<b>Problema y público.</b> El GeoJSON contiene miles de registros que no son cómodos de inspeccionar fila por fila. El tablero organiza esa información en un mapa, KPIs y gráficos para estudiantes, analistas y equipos que necesitan explorar datos viales públicos. El resultado es exploratorio y no sustituye información oficial ni una decisión de ingeniería.",
        ],
    )
    story.append(Paragraph("Stack tecnológico", styles["Subsection"]))
    story.append(
        table(
            [
                ["Herramienta", "Uso"],
                ["Python y pandas", "Lectura de properties, transformación de tipos, filtros y resúmenes."],
                ["NumPy y scikit-learn", "Preparación numérica, MLPRegressor y métricas MAE/RMSE."],
                ["Dash y Plotly", "Aplicación web local, mapa, gráficos interactivos y filtros."],
                ["Matplotlib y Seaborn", "Gráficos estáticos complementarios."],
                ["ReportLab y Pillow", "Generación del documento y anotación de capturas."],
                ["Git y Docker", "Control local de versiones y alternativa de ejecución aislada."],
            ],
            [4.2 * cm, 13.6 * cm],
            styles,
        )
    )
    story.append(Paragraph("Instalación y ejecución para programadores", styles["Subsection"]))
    commands = (
        "python3 -m venv .venv\n"
        "source .venv/bin/activate\n"
        "pip install -r requirements.txt\n"
        "python app.py\n"
        "# abrir http://127.0.0.1:8050"
    )
    story.append(Paragraph(f"<font name='Courier'>{commands.replace(chr(10), '<br/>')}</font>", styles["SmallText"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("El GeoJSON ya está incluido. Para descargarlo de nuevo: <font name='Courier'>python src/download_data.py</font>. Para regenerar los gráficos: <font name='Courier'>python src/make_static_charts.py</font>. Para ver métricas en consola: <font name='Courier'>python src/analysis.py</font>.", styles["Body"]))
    story.append(PageBreak())

    add_section(
        story,
        styles,
        "2. Documentación técnica",
        [
            "<b>Estructura.</b> <font name='Courier'>app.py</font> inicia Dash y conecta filtros y gráficos; <font name='Courier'>src/analysis.py</font> contiene carga, limpieza, estadística y modelo; <font name='Courier'>src/download_data.py</font> descarga la fuente; <font name='Courier'>src/make_static_charts.py</font> genera visualizaciones estáticas; <font name='Courier'>src/generate_report.py</font> produce este PDF. El GeoJSON crudo está en <font name='Courier'>data/raw</font>, estilos y gráficos en <font name='Courier'>assets</font>, capturas en <font name='Courier'>screenshots</font> y el documento final en <font name='Courier'>output/pdf</font>.",
        ],
    )
    story.append(Paragraph("Pipeline de datos", styles["Subsection"]))
    story.append(pipeline_diagram())
    story.append(
        Paragraph(
            "El programa lee <font name='Courier'>features[].properties</font> con pandas, convierte campos numéricos, conserva faltantes y normaliza espacios en campos de texto. Los descriptivos y gráficos usan los registros disponibles. Para el modelo, las filas sin <font name='Courier'>distancia</font> quedan fuera del entrenamiento, sin imputación.",
            styles["Body"],
        )
    )
    story.append(Paragraph("Modelo analítico", styles["Subsection"]))
    story.append(
        Paragraph(
            "La tarea es regresión supervisada: estimar <font name='Courier'>distancia</font> con <font name='Courier'>progresiva</font>, <font name='Courier'>latitud</font> y <font name='Courier'>longitud</font>. Un MLP de scikit-learn usa dos capas ocultas (32 y 16 neuronas), activación ReLU, estandarización y un máximo de 300 iteraciones con parada temprana. El entrenamiento limita BLAS a dos hilos de CPU. Los campos <font name='Courier'>id</font>, <font name='Courier'>id_mojon</font> y <font name='Courier'>desc</font> se excluyen: son identificadores o <font name='Courier'>desc</font> repite la progresiva. <font name='Courier'>cod_ruta</font> se usa solo para separar grupos, no como predictor.",
            styles["Body"],
        )
    )
    story.append(
        Paragraph(
            f"Se reservó aproximadamente el 20% de las rutas completas (semilla 42): {len(model['test_routes'])} rutas y {fmt_int(model['test_rows'])} filas de prueba, sin compartir rutas con entrenamiento. La referencia base predice la mediana de distancia calculada en entrenamiento.",
            styles["Body"],
        )
    )
    story.append(
        table(
            [
                ["Método", "MAE", "RMSE"],
                ["Base: mediana del entrenamiento", fmt_decimal(model["baseline"]["mae"]), fmt_decimal(model["baseline"]["rmse"])],
                ["Red neuronal MLP", fmt_decimal(model["mlp"]["mae"]), fmt_decimal(model["mlp"]["rmse"])],
            ],
            [8.2 * cm, 4.8 * cm, 4.8 * cm],
            styles,
        )
    )
    story.append(
        Paragraph(
            "MAE es el error absoluto medio; RMSE penaliza más los errores grandes. Menor es mejor. Los valores se expresan en la escala publicada para la columna distancia; no se asigna una unidad no confirmada por el archivo. La comparación es una evaluación académica sobre este dataset, no una promesa de desempeño futuro.",
            styles["SmallText"],
        )
    )
    story.append(Paragraph("Guía de estilo", styles["Subsection"]))
    story.append(
        table(
            [
                ["Elemento", "Definición"],
                ["Tema", "Operativo y sobrio; fondo papel, paneles claros y jerarquía tipográfica simple."],
                ["Paleta", "Tinta #18201f; fondo #f6f2e9; panel #fffdf8; verde #106b5f; acento #d04f2f."],
                ["Tipografía", "Avenir; alternativas Helvetica Neue y Helvetica."],
            ],
            [3.6 * cm, 14.2 * cm],
            styles,
        )
    )
    story.append(PageBreak())

    add_section(
        story,
        styles,
        "3. Gobierno de datos",
        [
            f"<b>Fuente.</b> GeoJSON público de IDE Transporte, capa <font name='Courier'>observ:_3.4.1.1.4.poste_1km_2018</font>. <link href='{DATA_URL_HTML}' color='#106b5f'>Abrir el servicio WFS de IDE Transporte</link>. Se conserva la fuente cruda en <font name='Courier'>data/raw/postes_1km_2018.geojson</font>.",
            "<b>Transformación con pandas.</b> Cada feature se convierte desde <font name='Courier'>properties</font> a una fila. Los campos numéricos se convierten con <font name='Courier'>pd.to_numeric(errors='coerce')</font>; los campos textuales se limpian con <font name='Courier'>strip()</font>. No se eliminan registros del DataFrame ni se imputan distancias. La red usa solo las filas con objetivo y predictores válidos.",
        ],
    )
    story.append(
        table(
            [
                ["Control sobre el archivo", "Resultado"],
                ["Features", fmt_int(summary["records"])],
                ["Rutas y distritos", f"{summary['routes']} rutas; {summary['districts']} distritos"],
                ["Progresiva", f"media {fmt_one(summary['progressiva_mean'])}; mediana {fmt_one(summary['progressiva_median'])}; Q1 {fmt_one(summary['progressiva_q1'])}; Q3 {fmt_one(summary['progressiva_q3'])}; desvío {fmt_one(summary['progressiva_std'])}; rango {fmt_one(summary['progressiva_min'])} a {fmt_one(summary['progressiva_max'])} km"],
                ["Distancia", f"{fmt_int(model['target_rows'])} completas; {fmt_int(quality['missing_distance'])} faltantes ({fmt_decimal(100 * quality['missing_distance'] / summary['records'])}%)"],
                ["Año de ruta", "2016 en los 27.143 registros; no hay variación temporal para pronosticar años."],
                ["Validación de coordenadas", f"{quality['coordinates_out_of_range']} registros fuera de latitud/longitud válidas."],
                ["IDs y duplicados", f"{quality['duplicate_id']} IDs de registro repetidos; {fmt_int(quality['desc_equals_progressiva'])} descripciones coinciden con progresiva."],
            ],
            [5.2 * cm, 12.6 * cm],
            styles,
        )
    )
    story.append(Paragraph("Diccionario de datos", styles["Subsection"]))
    dictionary = [
        ["Campo", "Descripción y uso"],
        ["id", "Identificador del registro en la fuente; no es predictor."],
        ["id_mojon", "Identificador del mojón o poste; se excluye del modelo."],
        ["cod_ruta", "Código de ruta; filtro del tablero y clave para separar train/test."],
        ["latitud", "Coordenada geográfica; predictor numérico del MLP."],
        ["longitud", "Coordenada geográfica; predictor numérico del MLP."],
        ["progresiva", "Kilómetro o avance sobre la ruta; filtro, estadística y predictor."],
        ["ano_ruta", "Año informado para la ruta; 2016 en este archivo."],
        ["distancia", "Campo numérico objetivo para el modelo; contiene valores faltantes."],
        ["desc", "Descripción corta; coincide con progresiva en los 27.143 registros."],
        ["distrito", "Distrito o jurisdicción; filtro y dimensión descriptiva."],
    ]
    story.append(table(dictionary, [3.2 * cm, 14.6 * cm], styles))
    story.append(PageBreak())

    add_section(
        story,
        styles,
        "4. Guía de usuario",
        [
            "<b>Glosario.</b> <b>Poste:</b> registro georreferenciado de un punto kilométrico. <b>Ruta:</b> código vial. <b>Distrito:</b> jurisdicción asociada. <b>Progresiva:</b> kilometraje o avance informado. <b>MAE:</b> promedio del valor absoluto de los errores de predicción. <b>RMSE:</b> raíz del promedio del error al cuadrado, más sensible a errores grandes. <b>Línea base:</b> mediana de distancia del conjunto de entrenamiento.",
            "<b>Navegación.</b> Elegí uno o más distritos y códigos de ruta en los menús; ajustá el control de progresiva. Las tarjetas de KPI, el mapa y los dos gráficos superiores responden a los filtros. Si limpiás un menú, el tablero muestra todos los valores de esa dimensión.",
            "<b>Modelo.</b> El panel de análisis es global y no cambia con los filtros del mapa. Muestra el número de registros completos, las rutas reservadas, MAE de la red y mediana de progresiva. En el gráfico de comparación, cada punto corresponde a un caso de prueba; la diagonal punteada representa una estimación igual al valor real. El histograma resume la progresiva de todo el archivo.",
        ],
    )
    story.append(Paragraph("Preguntas frecuentes", styles["Subsection"]))
    story.append(
        table(
            [
                ["Pregunta", "Respuesta"],
                ["¿Por qué algunas distancias no entran al modelo?", "La fuente tiene 2.415 objetivos faltantes. Se conservan en el tablero y se excluyen del entrenamiento y evaluación."],
                ["¿El MLP predice el futuro?", "No. El archivo registra 2016 para todas las rutas. El modelo estima una columna existente y no es un pronóstico temporal."],
                ["¿Por qué la red usa rutas reservadas?", "Para medir desempeño en rutas que no aportaron ejemplos al entrenamiento y reducir fuga de información entre filas de una misma ruta."],
                ["¿Qué significa un MAE menor?", "Que el promedio de errores absolutos es más bajo en las unidades de la columna distancia."],
                ["¿Qué hago si falta el GeoJSON o el gráfico?", "Ejecutá <font name='Courier'>python src/download_data.py</font> para bajar la fuente y <font name='Courier'>python src/make_static_charts.py</font> para recrear gráficos estáticos."],
                ["¿Cómo regenero la documentación?", "Ejecutá <font name='Courier'>python -m src.generate_report</font> después de instalar requirements.txt."],
            ],
            [6.4 * cm, 11.4 * cm],
            styles,
        )
    )
    story.append(Spacer(1, 0.25 * cm))
    story.append(
        Paragraph(
            f"Código de esta entrega: <link href='{REPOSITORY_URL}' color='#106b5f'>rama codex/poad-parcial2-analisis</link> del repositorio público. El enlace abre esta versión del código.",
            styles["SmallText"],
        )
    )
    story.append(Spacer(1, 0.15 * cm))
    story.append(
        Paragraph(
            "Referencias: <link href='https://scikit-learn.org/stable/modules/neural_networks_supervised.html' color='#106b5f'>Documentación oficial de redes neuronales supervisadas de scikit-learn</link>; <link href='https://pandas.pydata.org/docs/' color='#106b5f'>documentación de pandas</link>; material bibliográfico indicado en la consigna.",
            styles["SmallText"],
        )
    )
    story.append(PageBreak())

    add_section(
        story,
        styles,
        "5. Captura del dashboard",
        [
            "La imagen muestra la vista principal. Los números marcan dónde están los controles y resultados interactivos.",
        ],
    )
    story.append(fitted_image(SCREENSHOT_OVERVIEW, width_cm=16.8))
    story.append(Spacer(1, 0.3 * cm))
    story.append(
        table(
            [
                ["N°", "Elemento"],
                ["1", "Rango de progresiva y filtros de distrito/ruta."],
                ["2", "Filtro de distrito."],
                ["3", "Filtro de ruta."],
                ["4", "KPIs recalculados según la selección."],
            ],
            [1.1 * cm, 16.7 * cm],
            styles,
        )
    )
    story.append(PageBreak())

    add_section(
        story,
        styles,
        "6. Captura de gráficos interactivos",
        [
            "El mapa y los gráficos de barras pertenecen a la selección activa. El mapa puede mostrar una muestra reproducible de hasta 5.000 puntos para mantener fluidez.",
        ],
    )
    story.append(fitted_image(SCREENSHOT_CHARTS, width_cm=16.8))
    story.append(Spacer(1, 0.3 * cm))
    story.append(
        table(
            [
                ["N°", "Elemento"],
                ["1", "Mapa geográfico de postes y leyenda por código de ruta."],
                ["2", "Barras horizontales con el top 12 de distritos."],
                ["3", "Barras verticales con el top 12 de rutas."],
            ],
            [1.1 * cm, 16.7 * cm],
            styles,
        )
    )
    story.append(PageBreak())

    add_section(
        story,
        styles,
        "7. Captura del análisis",
        [
            "El panel inferior resume la evaluación por rutas completas. Las métricas provienen del conjunto de prueba y son independientes de los filtros del mapa.",
        ],
    )
    story.append(fitted_image(SCREENSHOT_ANALYSIS, width_cm=16.8))
    story.append(Spacer(1, 0.3 * cm))
    story.append(
        table(
            [
                ["N°", "Elemento"],
                ["1", "Resumen estadístico y número de rutas reservadas."],
                ["2", "MAE de la red y valor de referencia de la base mediana."],
                ["3", "Comparación de predicción vs. valor real; cuanto más cerca de la diagonal, menor error."],
                ["4", "Distribución de progresivas del GeoJSON."],
            ],
            [1.1 * cm, 16.7 * cm],
            styles,
        )
    )
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        Paragraph(
            f"Resultado de esta ejecución: MAE MLP {fmt_decimal(model['mlp']['mae'])} frente a {fmt_decimal(model['baseline']['mae'])} de la base; RMSE MLP {fmt_decimal(model['mlp']['rmse'])} frente a {fmt_decimal(model['baseline']['rmse'])}. La métrica no garantiza el mismo resultado con otra descarga o en otros datos.",
            styles["SmallText"],
        )
    )

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"PDF generado: {OUT}")


if __name__ == "__main__":
    main()
