#!/usr/bin/env python3
"""Pipeline reprodutível de regressão e monitoramento offline do UCI Bike Sharing.

Os dados são baixados da fonte oficial na primeira execução e permanecem em data/,
que está no .gitignore. Nenhuma observação é gerada ou alterada.
"""
from __future__ import annotations

import json
import sys
import unittest
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
ARCHIVE_PATH = DATA_DIR / "bike-sharing-dataset.zip"
DATA_URL = "https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip"
DATASET_PAGE = "https://archive.ics.uci.edu/ml/datasets/bike+sharing+dataset"

TARGET = "cnt"
CATEGORICAL_FEATURES = [
    "season", "yr", "mnth", "hr", "holiday", "weekday", "workingday", "weathersit"
]
NUMERIC_FEATURES = ["temp", "atemp", "hum", "windspeed"]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
REQUIRED_COLUMNS = {
    "instant", "dteday", "season", "yr", "mnth", "hr", "holiday", "weekday",
    "workingday", "weathersit", "temp", "atemp", "hum", "windspeed",
    "casual", "registered", "cnt",
}


def download_archive() -> Path:
    """Baixa e valida o ZIP oficial apenas quando ainda não está em cache."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if ARCHIVE_PATH.exists() and zipfile.is_zipfile(ARCHIVE_PATH):
        return ARCHIVE_PATH

    request = urllib.request.Request(
        DATA_URL,
        headers={"User-Agent": "10-mlops-monitoramento/1.0 (reproducible portfolio analysis)"},
    )
    temporary_path = ARCHIVE_PATH.with_suffix(".zip.part")
    try:
        with urllib.request.urlopen(request, timeout=180) as response, temporary_path.open("wb") as output:
            if response.status != 200:
                raise RuntimeError(f"Download UCI respondeu HTTP {response.status}.")
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)
        if not zipfile.is_zipfile(temporary_path):
            raise RuntimeError("O arquivo baixado da fonte oficial não é um ZIP válido.")
        temporary_path.replace(ARCHIVE_PATH)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
    return ARCHIVE_PATH


def load_dataset() -> pd.DataFrame:
    archive_path = download_archive()
    with zipfile.ZipFile(archive_path) as archive:
        member = next((name for name in archive.namelist() if name.lower().endswith("hour.csv")), None)
        if member is None:
            raise RuntimeError("O ZIP oficial não contém hour.csv.")
        with archive.open(member) as csv_file:
            frame = pd.read_csv(csv_file)
    return validate_dataset(frame)


def validate_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    """Aplica verificações de esquema, integridade, intervalos e cronologia."""
    missing_columns = REQUIRED_COLUMNS - set(frame.columns)
    if missing_columns:
        raise ValueError(f"Colunas obrigatórias ausentes: {sorted(missing_columns)}")
    if frame.empty:
        raise ValueError("Dataset vazio.")
    if frame[list(REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError("Há valores ausentes em colunas obrigatórias.")
    if frame["instant"].duplicated().any():
        raise ValueError("O identificador instant não é único.")

    numeric_columns = sorted(REQUIRED_COLUMNS - {"dteday"})
    numeric_values = frame[numeric_columns].to_numpy(dtype=float)
    if not np.isfinite(numeric_values).all():
        raise ValueError("Há valores não finitos em colunas numéricas.")
    if (frame[["cnt", "casual", "registered"]] < 0).any().any():
        raise ValueError("Contagens negativas foram encontradas.")
    if not (frame["cnt"] == frame["casual"] + frame["registered"]).all():
        raise ValueError("A relação cnt = casual + registered falhou.")
    if not frame["season"].isin([1, 2, 3, 4]).all():
        raise ValueError("Valor de season fora do domínio documentado.")
    if not frame["hr"].between(0, 23).all():
        raise ValueError("Valor de hr fora do intervalo [0, 23].")
    if not frame["weathersit"].isin([1, 2, 3, 4]).all():
        raise ValueError("Valor de weathersit fora do domínio documentado.")

    parsed_date = pd.to_datetime(frame["dteday"], errors="raise")
    result = frame.copy()
    result["timestamp"] = parsed_date + pd.to_timedelta(result["hr"], unit="h")
    if result["timestamp"].duplicated().any():
        raise ValueError("Há horários duplicados.")
    return result.sort_values("timestamp", kind="mergesort").reset_index(drop=True)


def chronological_split(frame: pd.DataFrame, train_fraction: float = 0.8) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not 0.5 <= train_fraction < 1.0:
        raise ValueError("train_fraction deve estar entre 0,5 e 1,0.")
    split_index = int(len(frame) * train_fraction)
    if split_index == 0 or split_index == len(frame):
        raise ValueError("Não há amostras suficientes para a divisão temporal.")
    train = frame.iloc[:split_index].copy()
    test = frame.iloc[split_index:].copy()
    if train["timestamp"].max() >= test["timestamp"].min():
        raise ValueError("A divisão temporal não preservou a ordem cronológica.")
    return train, test


def build_model() -> Pipeline:
    categorical = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    numeric = Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))])
    preprocessing = ColumnTransformer(
        transformers=[
            ("categorical", categorical, CATEGORICAL_FEATURES),
            ("numeric", numeric, NUMERIC_FEATURES),
        ]
    )
    estimator = RandomForestRegressor(
        n_estimators=120,
        min_samples_leaf=2,
        max_features=0.8,
        random_state=42,
        n_jobs=-1,
    )
    return Pipeline(steps=[("preprocessing", preprocessing), ("model", estimator)])


def population_stability_index(reference: pd.Series, current: pd.Series, bins: int = 10) -> float:
    """PSI numérico com cortes quantílicos aprendidos apenas na referência."""
    reference_values = np.asarray(reference, dtype=float)
    current_values = np.asarray(current, dtype=float)
    if not np.isfinite(reference_values).all() or not np.isfinite(current_values).all():
        raise ValueError("PSI exige valores numéricos finitos.")
    edges = np.unique(np.quantile(reference_values, np.linspace(0, 1, bins + 1)))
    if len(edges) < 2:
        return 0.0 if np.all(current_values == reference_values[0]) else float("inf")
    edges[0], edges[-1] = -np.inf, np.inf
    reference_counts = np.histogram(reference_values, bins=edges)[0].astype(float)
    current_counts = np.histogram(current_values, bins=edges)[0].astype(float)
    epsilon = 1e-6
    reference_share = (reference_counts + epsilon) / (len(reference_values) + epsilon * len(reference_counts))
    current_share = (current_counts + epsilon) / (len(current_values) + epsilon * len(current_counts))
    return float(np.sum((current_share - reference_share) * np.log(current_share / reference_share)))


def categorical_total_variation(reference: pd.Series, current: pd.Series) -> float:
    """Distância de variação total entre frequências categóricas (intervalo 0–1)."""
    reference_counts = reference.value_counts(normalize=True, dropna=False)
    current_counts = current.value_counts(normalize=True, dropna=False)
    categories = reference_counts.index.union(current_counts.index)
    p = reference_counts.reindex(categories, fill_value=0.0).to_numpy(dtype=float)
    q = current_counts.reindex(categories, fill_value=0.0).to_numpy(dtype=float)
    return float(0.5 * np.abs(p - q).sum())


def metric_bundle(actual: pd.Series, predicted: np.ndarray) -> dict[str, float]:
    values = {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
    }
    if not all(np.isfinite(value) for value in values.values()):
        raise RuntimeError("Uma métrica de avaliação não é finita.")
    return values


def run_real_data_tests(frame: pd.DataFrame, train: pd.DataFrame, test: pd.DataFrame) -> unittest.TestResult:
    """Executa testes automatizados usando exclusivamente amostras da fonte UCI."""

    class RealDatasetTests(unittest.TestCase):
        def test_required_schema_and_values(self) -> None:
            self.assertTrue(REQUIRED_COLUMNS.issubset(frame.columns))
            self.assertFalse(frame[list(REQUIRED_COLUMNS)].isna().any().any())
            self.assertTrue((frame["cnt"] == frame["casual"] + frame["registered"]).all())

        def test_target_components_are_not_features(self) -> None:
            self.assertNotIn(TARGET, FEATURES)
            self.assertNotIn("casual", FEATURES)
            self.assertNotIn("registered", FEATURES)
            self.assertNotIn("instant", FEATURES)

        def test_time_split_is_forward_only(self) -> None:
            self.assertEqual(len(train) + len(test), len(frame))
            self.assertLess(train["timestamp"].max(), test["timestamp"].min())

        def test_drift_metrics_are_zero_on_same_real_reference(self) -> None:
            for feature in NUMERIC_FEATURES:
                self.assertAlmostEqual(population_stability_index(train[feature], train[feature]), 0.0, places=10)
            for feature in CATEGORICAL_FEATURES:
                self.assertAlmostEqual(categorical_total_variation(train[feature], train[feature]), 0.0, places=10)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RealDatasetTests)
    return unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)


def analyze() -> dict[str, Any]:
    frame = load_dataset()
    train, test = chronological_split(frame)
    test_result = run_real_data_tests(frame, train, test)
    if not test_result.wasSuccessful():
        raise RuntimeError("Os testes do dataset falharam; análise interrompida.")

    model = build_model()
    model.fit(train[FEATURES], train[TARGET])
    prediction = model.predict(test[FEATURES])
    model_metrics = metric_bundle(test[TARGET], prediction)

    baseline = DummyRegressor(strategy="median")
    baseline.fit(train[["instant"]], train[TARGET])
    baseline_prediction = baseline.predict(test[["instant"]])
    baseline_metrics = metric_bundle(test[TARGET], baseline_prediction)

    drift: list[dict[str, Any]] = []
    for feature in NUMERIC_FEATURES:
        value = population_stability_index(train[feature], test[feature])
        drift.append({
            "feature": feature,
            "measure": "PSI",
            "value": value,
            "threshold": 0.20,
            "alert": bool(value > 0.20),
        })
    for feature in CATEGORICAL_FEATURES:
        value = categorical_total_variation(train[feature], test[feature])
        drift.append({
            "feature": feature,
            "measure": "TV",
            "value": value,
            "threshold": 0.10,
            "alert": bool(value > 0.10),
        })

    return {
        "dataset": "UCI Bike Sharing, arquivo hour.csv",
        "source_page": DATASET_PAGE,
        "download_url": DATA_URL,
        "rows": int(len(frame)),
        "period": {
            "start": frame["timestamp"].min().isoformat(),
            "end": frame["timestamp"].max().isoformat(),
        },
        "split": {
            "protocol": "holdout cronológico, primeiros 80% para treino e últimos 20% para teste",
            "train_rows": int(len(train)),
            "test_rows": int(len(test)),
            "train_end": train["timestamp"].max().isoformat(),
            "test_start": test["timestamp"].min().isoformat(),
        },
        "features": FEATURES,
        "validation_tests": {
            "passed": bool(test_result.wasSuccessful()),
            "count": int(test_result.testsRun),
        },
        "quality": {
            "missing_values_in_required_columns": int(frame[list(REQUIRED_COLUMNS)].isna().sum().sum()),
            "duplicate_ids": int(frame["instant"].duplicated().sum()),
            "target_equals_casual_plus_registered": bool((frame[TARGET] == frame["casual"] + frame["registered"]).all()),
        },
        "baseline_median": baseline_metrics,
        "random_forest": model_metrics,
        "drift": drift,
        "drift_alerts": int(sum(item["alert"] for item in drift)),
    }


def main() -> None:
    results = analyze()
    print(json.dumps(results, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
