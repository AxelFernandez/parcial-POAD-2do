from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dcc, html


ROOT = Path(__file__).resolve().parent
RAW_DATA = ROOT / "data" / "raw" / "postes_1km_2018.geojson"


def cargar_geojson() -> pd.DataFrame:
    """Lee el GeoJSON crudo y arma un DataFrame con sus propiedades."""
    with RAW_DATA.open(encoding="utf-8") as file:
        geojson = json.load(file)

    filas = [feature["properties"] for feature in geojson["features"]]
    return pd.DataFrame(filas)


df = cargar_geojson()

app = Dash(__name__)
app.title = "Postes kilométricos"

DISTRICTS = sorted(df["distrito"].dropna().unique())
ROUTES = sorted(df["cod_ruta"].dropna().unique())
PROGRESS_MIN = int(df["progresiva"].min())
PROGRESS_MAX = int(df["progresiva"].max())

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
                            "El dashboard lee el GeoJSON crudo, parsea las propiedades de cada feature y usa pandas, matplotlib, seaborn y plotly para visualizar los datos."
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
                html.Div([html.Label("Distrito"), dcc.Dropdown(DISTRICTS, DISTRICTS, multi=True, id="district-filter")]),
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
        html.Div(
            className="static-gallery",
            children=[
                html.Div(
                    [
                        html.H2("Grafico estatico Matplotlib"),
                        html.Img(src="/assets/matplotlib_postes_distrito.png"),
                    ],
                    className="static-card",
                ),
                html.Div(
                    [
                        html.H2("Grafico estatico Seaborn"),
                        html.Img(src="/assets/seaborn_postes_ruta.png"),
                    ],
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
        ("Postes", f"{len(data):,}".replace(",", "."), "Registros filtrados"),
        ("Rutas", data["cod_ruta"].nunique(), "Codigos distintos"),
        ("Distritos", data["distrito"].nunique(), "Jurisdicciones"),
        ("Progresiva max.", int(data["progresiva"].max()), "Valor mayor"),
    ]
    kpi_cards = [
        html.Div([html.Span(label), html.Strong(value), html.Small(note)], className="kpi-card")
        for label, value, note in kpis
    ]

    map_data = data
    if len(map_data) > 5000:
        map_data = data.sample(5000, random_state=7)

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

    for fig in [map_fig, district_fig, route_fig]:
        fig.update_layout(
            template="plotly_white",
            font_family="Avenir, Helvetica, sans-serif",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=40, r=24, t=56, b=40),
        )

    return kpi_cards, map_fig, district_fig, route_fig


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False, port=8050)
