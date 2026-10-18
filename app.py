from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html

from src.analysis import analyze_data, load_data


df = load_data()
analysis = analyze_data(df)
summary = analysis["summary"]
model_result = analysis["model"]

DISTRICTS = sorted(df["distrito"].dropna().unique())
ROUTES = sorted(df["cod_ruta"].dropna().unique())
PROGRESS_MIN = int(df["progresiva"].min())
PROGRESS_MAX = int(df["progresiva"].max())


def format_integer(value: int | float) -> str:
    return f"{int(value):,}".replace(",", ".")


def format_decimal(value: int | float) -> str:
    return f"{value:.1f}".replace(".", ",")


def model_figure() -> go.Figure:
    """Compara la red con la regla base en una muestra reproducible."""
    sample = model_result["predictions"].sample(
        n=min(1500, model_result["test_rows"]), random_state=42
    )
    low = float(sample["distancia_real"].min())
    high = float(sample["distancia_real"].max())
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=sample["distancia_real"],
            y=sample["prediccion_base"],
            mode="markers",
            name="Base mediana",
            opacity=0.45,
            marker={"color": "#d04f2f", "size": 6},
            customdata=sample["cod_ruta"],
            hovertemplate="Ruta %{customdata}<br>Real: %{x:.1f}<br>Base mediana: %{y:.1f}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=sample["distancia_real"],
            y=sample["prediccion_mlp"],
            mode="markers",
            name="Red MLP",
            opacity=0.45,
            marker={"color": "#106b5f", "size": 6},
            customdata=sample["cod_ruta"],
            hovertemplate="Ruta %{customdata}<br>Real: %{x:.1f}<br>MLP: %{y:.1f}<extra></extra>",
        )
    )
    figure.add_shape(
        type="line",
        x0=low,
        y0=low,
        x1=high,
        y1=high,
        line={"color": "#18201f", "dash": "dash", "width": 1},
    )
    figure.update_layout(
        title="Distancia real y estimada (rutas reservadas)",
        xaxis_title="Distancia real (valor de fuente)",
        yaxis_title="Distancia estimada (valor de fuente)",
        template="plotly_white",
        font_family="Avenir, Helvetica, sans-serif",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=52, r=24, t=56, b=48),
    )
    return figure


def progress_figure() -> go.Figure:
    figure = px.histogram(df, x="progresiva", nbins=32, title="Distribución de progresivas")
    figure.update_traces(marker_color="#106b5f")
    figure.update_layout(
        xaxis_title="Progresiva (km)",
        yaxis_title="Cantidad de postes",
        template="plotly_white",
        font_family="Avenir, Helvetica, sans-serif",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=52, r=24, t=56, b=48),
    )
    return figure


app = Dash(__name__)
app.title = "Postes kilométricos"

app.layout = html.Div(
    className="app-shell",
    children=[
        html.Div(
            className="topbar",
            children=[
                html.Div(
                    [
                        html.P("Dash + dataset real IDE Transporte", className="eyebrow"),
                        html.H1("Postes kilométricos"),
                        html.P(
                            "Explorá postes viales de IDE Transporte y compará una red neuronal "
                            "con una regla base sencilla."
                        ),
                    ],
                    className="brand",
                ),
                html.Div(
                    [
                        html.Label("Rango de progresiva"),
                        dcc.RangeSlider(
                            id="progress-filter",
                            min=PROGRESS_MIN,
                            max=PROGRESS_MAX,
                            value=[PROGRESS_MIN, PROGRESS_MAX],
                            step=50,
                            marks=None,
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),
                    ],
                    className="range-filter",
                ),
            ],
        ),
        html.Div(
            className="filters",
            children=[
                html.Div(
                    [html.Label("Distrito"), dcc.Dropdown(DISTRICTS, DISTRICTS, multi=True, id="district-filter")]
                ),
                html.Div([html.Label("Ruta"), dcc.Dropdown(ROUTES, ROUTES[:8], multi=True, id="route-filter")]),
            ],
        ),
        html.Div(id="kpi-row", className="kpi-row"),
        html.Div(
            className="grid",
            children=[
                html.Div([dcc.Graph(id="map-graph")], className="panel panel-wide"),
                html.Div([dcc.Graph(id="district-graph")], className="panel"),
                html.Div([dcc.Graph(id="route-graph")], className="panel"),
            ],
        ),
        html.Section(
            className="analysis-section",
            children=[
                html.Div(
                    [
                        html.P("ANÁLISIS ESTADÍSTICO", className="eyebrow"),
                        html.H2("¿Qué tan cerca está la distancia registrada?"),
                        html.P(
                            "La red estima distancia usando progresiva y coordenadas. La evaluación reserva "
                            "rutas completas; cada punto compara distancia real y predicción."
                        ),
                    ],
                    className="analysis-heading",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span("Distancia completa"),
                                html.Strong(format_integer(model_result["target_rows"])),
                                html.Small(f"de {format_integer(summary['records'])} registros"),
                            ],
                            className="analysis-card",
                        ),
                        html.Div(
                            [
                                html.Span("Rutas reservadas"),
                                html.Strong(str(len(model_result["test_routes"]))),
                                html.Small(f"{format_integer(model_result['test_rows'])} filas de prueba"),
                            ],
                            className="analysis-card",
                        ),
                        html.Div(
                            [
                                html.Span("MAE de la red"),
                                html.Strong(format_decimal(model_result["mlp"]["mae"])),
                                html.Small(f"Base mediana: {format_decimal(model_result['baseline']['mae'])}"),
                            ],
                            className="analysis-card",
                        ),
                        html.Div(
                            [
                                html.Span("Mediana de progresiva"),
                                html.Strong(f"{format_integer(summary['progressiva_median'])} km"),
                                html.Small(
                                    f"Rango {format_integer(summary['progressiva_min'])} a "
                                    f"{format_integer(summary['progressiva_max'])} km"
                                ),
                            ],
                            className="analysis-card",
                        ),
                    ],
                    className="analysis-kpi-row",
                ),
                html.Div(
                    [
                        dcc.Graph(id="model-graph", figure=model_figure()),
                        dcc.Graph(id="progressiva-graph", figure=progress_figure()),
                    ],
                    className="analysis-grid",
                ),
                html.P(
                    "La regla base predice la mediana de distancia del entrenamiento. El MAE resume el error "
                    "absoluto medio en la escala de la columna distancia; un valor menor indica predicciones más cercanas. El análisis excluye "
                    "distancias faltantes y no imputa valores. Las métricas son globales y no cambian con los filtros.",
                    className="analysis-note",
                ),
            ],
        ),
        html.Div(
            className="static-gallery",
            children=[
                html.Div(
                    [html.H2("Gráfico estático Matplotlib"), html.Img(src="/assets/matplotlib_postes_distrito.png")],
                    className="static-card",
                ),
                html.Div(
                    [html.H2("Gráfico estático Seaborn"), html.Img(src="/assets/seaborn_postes_ruta.png")],
                    className="static-card",
                ),
            ],
        ),
    ],
)


def filtrar_datos(districts: list[str], routes: list[str], progress_range: list[int]) -> pd.DataFrame:
    desde, hasta = progress_range
    return df[
        (df["distrito"].isin(districts or DISTRICTS))
        & (df["cod_ruta"].isin(routes or ROUTES))
        & (df["progresiva"].between(desde, hasta))
    ]


@app.callback(
    Output("kpi-row", "children"),
    Output("map-graph", "figure"),
    Output("district-graph", "figure"),
    Output("route-graph", "figure"),
    Input("district-filter", "value"),
    Input("route-filter", "value"),
    Input("progress-filter", "value"),
)
def actualizar_dashboard(districts, routes, progress_range):
    data = filtrar_datos(districts, routes, progress_range)

    if data.empty:
        empty = px.scatter(title="Sin datos para los filtros seleccionados")
        return [html.Div("Sin datos", className="kpi-card")], empty, empty, empty

    kpis = [
        ("Postes", format_integer(len(data)), "Registros filtrados"),
        ("Rutas", data["cod_ruta"].nunique(), "Códigos distintos"),
        ("Distritos", data["distrito"].nunique(), "Jurisdicciones"),
        ("Progresiva máx.", format_integer(data["progresiva"].max()), "Valor mayor"),
    ]
    kpi_cards = [
        html.Div([html.Span(label), html.Strong(value), html.Small(note)], className="kpi-card")
        for label, value, note in kpis
    ]

    map_data = data.sample(5000, random_state=7) if len(data) > 5000 else data
    map_fig = px.scatter_geo(
        map_data,
        lat="latitud",
        lon="longitud",
        color="cod_ruta",
        hover_name="distrito",
        hover_data=["cod_ruta", "progresiva", "distancia"],
        title="Mapa interactivo de postes",
    )
    map_fig.update_geos(
        projection_type="mercator",
        center={"lat": -38, "lon": -64},
        lonaxis_range=[-74, -52],
        lataxis_range=[-56, -20],
        showland=True,
        landcolor="#f6f2e9",
        showcountries=True,
        countrycolor="#b8b0a1",
    )

    by_district = data["distrito"].value_counts().head(12).reset_index()
    by_district.columns = ["distrito", "postes"]
    district_fig = px.bar(
        by_district.sort_values("postes"),
        x="postes",
        y="distrito",
        orientation="h",
        title="Top distritos por cantidad de postes",
    )

    by_route = data["cod_ruta"].value_counts().head(12).reset_index()
    by_route.columns = ["cod_ruta", "postes"]
    route_fig = px.bar(by_route, x="cod_ruta", y="postes", title="Top rutas por cantidad de postes")

    for figure in [map_fig, district_fig, route_fig]:
        figure.update_layout(
            template="plotly_white",
            font_family="Avenir, Helvetica, sans-serif",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=40, r=24, t=56, b=40),
        )

    return kpi_cards, map_fig, district_fig, route_fig


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False, port=8050)
