from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[1]
RAW_DATA = ROOT / "data" / "raw" / "postes_1km_2018.geojson"
ASSETS = ROOT / "assets"


def cargar_geojson() -> pd.DataFrame:
    with RAW_DATA.open(encoding="utf-8") as file:
        geojson = json.load(file)

    filas = [feature["properties"] for feature in geojson["features"]]
    return pd.DataFrame(filas)


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    df = cargar_geojson()

    top_districts = df["distrito"].value_counts().head(10).sort_values()
    top_routes = df["cod_ruta"].value_counts().head(12).reset_index()
    top_routes.columns = ["cod_ruta", "postes"]

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(top_districts.index, top_districts.values, color="#126c63")
    ax.set_title("Postes por distrito - Matplotlib")
    ax.set_xlabel("Cantidad de postes")
    ax.set_ylabel("Distrito")
    fig.tight_layout()
    fig.savefig(ASSETS / "matplotlib_postes_distrito.png", dpi=180)
    plt.close(fig)

    sns.set_theme(style="whitegrid", font="DejaVu Sans")
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=top_routes, x="cod_ruta", y="postes", hue="cod_ruta", palette="crest", ax=ax, legend=False)
    ax.set_title("Rutas con mas postes - Seaborn")
    ax.set_xlabel("Codigo de ruta")
    ax.set_ylabel("Cantidad de postes")
    fig.tight_layout()
    fig.savefig(ASSETS / "seaborn_postes_ruta.png", dpi=180)
    plt.close(fig)

    print("Graficos estaticos generados desde el GeoJSON crudo.")


if __name__ == "__main__":
    main()
