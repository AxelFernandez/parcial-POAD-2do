from __future__ import annotations

from pathlib import Path
from urllib.request import urlretrieve


URL = (
    "https://ide.transporte.gob.ar/geoserver/observ/ows?"
    "service=WFS&version=1.0.0&request=GetFeature"
    "&typeName=observ:_3.4.1.1.4.poste_1km_2018"
    "&maxFeatures=28000&outputFormat=application%2Fjson"
)

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "postes_1km_2018.geojson"


def main() -> None:
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    urlretrieve(URL, RAW_PATH)
    print(f"Dataset descargado: {RAW_PATH}")


if __name__ == "__main__":
    main()
