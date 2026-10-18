"""Carga, describe y modela el conjunto de postes kilometricos."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupShuffleSplit
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits


ROOT = Path(__file__).resolve().parents[1]
RAW_DATA = ROOT / "data" / "raw" / "postes_1km_2018.geojson"
NUMERIC_COLUMNS = ["id", "id_mojon", "latitud", "longitud", "progresiva", "ano_ruta", "distancia"]
MODEL_FEATURES = ["progresiva", "latitud", "longitud"]


def load_data(path: Path = RAW_DATA) -> pd.DataFrame:
    """Convierte las propiedades del GeoJSON a columnas pandas tipadas.

    Se conservan las filas con distancia faltante para que sigan disponibles
    en el dashboard descriptivo. El modelo excluye esas filas al entrenar.
    """
    with path.open(encoding="utf-8") as source:
        geojson = json.load(source)

    frame = pd.DataFrame([feature.get("properties", {}) for feature in geojson.get("features", [])])
    for column in NUMERIC_COLUMNS:
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    for column in ("cod_ruta", "distrito", "desc"):
        if column in frame:
            frame[column] = frame[column].astype("string").str.strip()
    return frame


def descriptive_summary(data: pd.DataFrame) -> dict[str, float | int]:
    """Calcula indicadores descriptivos sin imputar valores de la fuente."""
    progressiva = data["progresiva"].dropna()
    distancia = data["distancia"].dropna()
    progressiva_values = progressiva.to_numpy(dtype=float)
    distance_values = distancia.to_numpy(dtype=float)
    missing_distance = int(data["distancia"].isna().sum())
    total = int(len(data))

    return {
        "records": total,
        "routes": int(data["cod_ruta"].nunique()),
        "districts": int(data["distrito"].nunique()),
        "missing_distance": missing_distance,
        "distance_coverage_pct": round((total - missing_distance) * 100 / total, 1) if total else 0.0,
        "progressiva_mean": round(float(np.mean(progressiva_values)), 1) if len(progressiva_values) else 0.0,
        "progressiva_median": round(float(np.median(progressiva_values)), 1) if len(progressiva_values) else 0.0,
        "progressiva_std": round(float(np.std(progressiva_values, ddof=1)), 1) if len(progressiva_values) > 1 else 0.0,
        "progressiva_q1": round(float(np.percentile(progressiva_values, 25)), 1) if len(progressiva_values) else 0.0,
        "progressiva_q3": round(float(np.percentile(progressiva_values, 75)), 1) if len(progressiva_values) else 0.0,
        "progressiva_min": round(float(np.min(progressiva_values)), 1) if len(progressiva_values) else 0.0,
        "progressiva_max": round(float(np.max(progressiva_values)), 1) if len(progressiva_values) else 0.0,
        "distance_mean": round(float(np.mean(distance_values)), 1) if len(distance_values) else 0.0,
        "distance_median": round(float(np.median(distance_values)), 1) if len(distance_values) else 0.0,
    }


def train_distance_model(data: pd.DataFrame, max_iter: int = 300) -> dict:
    """Evalua una red MLP y una linea base en rutas reservadas completas.

    El objetivo es la columna distancia. La linea base predice la mediana del
    conjunto de entrenamiento, una referencia sencilla que no asume que las
    unidades de progresiva y distancia sean iguales.
    """
    required = MODEL_FEATURES + ["distancia", "cod_ruta"]
    model_data = data[required].replace([np.inf, -np.inf], np.nan).dropna().copy()
    if model_data["cod_ruta"].nunique() < 2 or len(model_data) < 10:
        raise ValueError("Se necesitan al menos dos rutas y diez distancias para evaluar el modelo.")

    features = model_data[MODEL_FEATURES].to_numpy(dtype=float)
    target = model_data["distancia"].to_numpy(dtype=float)
    routes = model_data["cod_ruta"].astype(str).to_numpy()

    split = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_index, test_index = next(split.split(features, target, groups=routes))
    x_train, x_test = features[train_index], features[test_index]
    y_train, y_test = target[train_index], target[test_index]

    target_scaler = StandardScaler()
    y_train_scaled = target_scaler.fit_transform(y_train.reshape(-1, 1)).ravel()
    model = make_pipeline(
        StandardScaler(),
        MLPRegressor(
            hidden_layer_sizes=(32, 16),
            activation="relu",
            solver="adam",
            alpha=0.01,
            batch_size=256,
            learning_rate_init=0.001,
            max_iter=max_iter,
            early_stopping=True,
            validation_fraction=0.15,
            n_iter_no_change=20,
            random_state=42,
        ),
    )
    with threadpool_limits(limits=2):
        model.fit(x_train, y_train_scaled)
    predicted = target_scaler.inverse_transform(model.predict(x_test).reshape(-1, 1)).ravel()
    baseline_model = DummyRegressor(strategy="median")
    baseline_model.fit(x_train, y_train)
    baseline = baseline_model.predict(x_test)

    def metrics(values: np.ndarray) -> dict[str, float]:
        return {
            "mae": round(float(mean_absolute_error(y_test, values)), 2),
            "rmse": round(float(np.sqrt(mean_squared_error(y_test, values))), 2),
        }

    test_rows = model_data.iloc[test_index]
    predictions = pd.DataFrame(
        {
            "cod_ruta": test_rows["cod_ruta"].astype(str).to_numpy(),
            "progresiva": x_test[:, 0],
            "distancia_real": y_test,
            "prediccion_base": baseline,
            "prediccion_mlp": predicted,
        }
    ).reset_index(drop=True)

    return {
        "target_rows": int(len(model_data)),
        "train_rows": int(len(train_index)),
        "test_rows": int(len(test_index)),
        "train_routes": sorted(set(routes[train_index])),
        "test_routes": sorted(set(routes[test_index])),
        "baseline": metrics(baseline),
        "mlp": metrics(predicted),
        "iterations": int(model[-1].n_iter_),
        "predictions": predictions,
    }


def analyze_data(data: pd.DataFrame) -> dict:
    """Devuelve las estadisticas descriptivas y la evaluacion de la red."""
    return {"summary": descriptive_summary(data), "model": train_distance_model(data)}


def main() -> None:
    data = load_data()
    result = analyze_data(data)
    summary = result["summary"]
    model = result["model"]
    print(f"Registros: {summary['records']:,}; rutas: {summary['routes']}; distritos: {summary['districts']}")
    print(f"Distancias completas: {model['target_rows']:,}; rutas de prueba: {len(model['test_routes'])}")
    print(f"MAE base: {model['baseline']['mae']}; MAE MLP: {model['mlp']['mae']}")
    print(f"RMSE base: {model['baseline']['rmse']}; RMSE MLP: {model['mlp']['rmse']}")


if __name__ == "__main__":
    main()
