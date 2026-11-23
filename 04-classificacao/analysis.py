#!/usr/bin/env python3
"""Classificação da qualidade do vinho tinto UCI com escolha de limiar na validação.

O arquivo oficial é baixado para data/cache/ na primeira execução. O modelo e o
limiar são escolhidos sem consultar o conjunto de teste.
"""
from __future__ import annotations

import hashlib
import io
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parent
CACHE_DIR = ROOT / "data" / "cache"
ARCHIVE_PATH = CACHE_DIR / "wine-quality.zip"
CSV_PATH = CACHE_DIR / "winequality-red.csv"
DATA_URL = "https://archive.ics.uci.edu/static/public/186/wine+quality.zip"
RANDOM_STATE_TEST = 42
RANDOM_STATE_VALIDATION = 43
POSITIVE_QUALITY_MIN = 7


def get_red_wine_csv() -> Path:
    """Obtain the red-wine CSV from UCI, caching the downloaded source archive."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if not ARCHIVE_PATH.exists():
        request = urllib.request.Request(
            DATA_URL, headers={"User-Agent": "04-classificacao-portfolio/1.0"}
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            archive_bytes = response.read()
        if not archive_bytes.startswith(b"PK\x03\x04"):
            raise RuntimeError("A resposta da UCI não parece ser um arquivo ZIP válido.")
        ARCHIVE_PATH.write_bytes(archive_bytes)

    if not CSV_PATH.exists():
        with zipfile.ZipFile(ARCHIVE_PATH) as archive:
            member = next(
                (name for name in archive.namelist() if name.endswith("winequality-red.csv")),
                None,
            )
            if member is None:
                raise RuntimeError("O ZIP oficial não contém winequality-red.csv.")
            # Extrai somente o arquivo esperado, sem gravar caminhos do ZIP.
            CSV_PATH.write_bytes(archive.read(member))
    return CSV_PATH


def choose_f1_threshold(y_true: pd.Series, probabilities: np.ndarray) -> tuple[float, float]:
    """Choose the validation threshold maximizing F1; break ties toward higher threshold."""
    candidates = np.unique(probabilities)
    scores = np.array(
        [f1_score(y_true, probabilities >= threshold, zero_division=0) for threshold in candidates]
    )
    best_f1 = float(scores.max())
    best_threshold = float(candidates[scores == scores.max()].max())
    return best_threshold, best_f1


def report_metrics(label: str, y_true: pd.Series, probabilities: np.ndarray, threshold: float) -> dict:
    predictions = probabilities >= threshold
    tn, fp, fn, tp = confusion_matrix(y_true, predictions, labels=[0, 1]).ravel()
    metrics = {
        "threshold": float(threshold),
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, predictions)),
        "roc_auc": float(roc_auc_score(y_true, probabilities)),
        "average_precision": float(average_precision_score(y_true, probabilities)),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }
    print(f"\n{label}")
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    return metrics


def main() -> None:
    csv_path = get_red_wine_csv()
    archive_sha256 = hashlib.sha256(ARCHIVE_PATH.read_bytes()).hexdigest()
    data = pd.read_csv(csv_path, sep=";")

    if "quality" not in data.columns or data.empty:
        raise ValueError("CSV inesperado: coluna quality ausente ou arquivo vazio.")
    if data.isna().any().any():
        raise ValueError("O dataset contém valores ausentes, ao contrário do esperado.")

    y = (data["quality"] >= POSITIVE_QUALITY_MIN).astype("int8")
    X = data.drop(columns="quality")

    # Primeiro separam-se 20% de teste; os 80% restantes são divididos em 75/25,
    # resultando em 60% treino, 20% validação e 20% teste. Todas as partições são estratificadas.
    X_dev, X_test, y_dev, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_STATE_TEST, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_dev,
        y_dev,
        test_size=0.25,
        random_state=RANDOM_STATE_VALIDATION,
        stratify=y_dev,
    )

    model = Pipeline(
        steps=[
            ("scale", StandardScaler()),
            ("logistic", LogisticRegression(max_iter=3000, solver="lbfgs", random_state=42)),
        ]
    )
    model.fit(X_train, y_train)
    validation_probabilities = model.predict_proba(X_val)[:, 1]
    chosen_threshold, validation_f1 = choose_f1_threshold(y_val, validation_probabilities)
    test_probabilities = model.predict_proba(X_test)[:, 1]

    print("Fonte: UCI Machine Learning Repository — Wine Quality (vinho tinto)")
    print(f"URL de download: {DATA_URL}")
    print(f"SHA-256 do ZIP baixado: {archive_sha256}")
    print(f"Versões: pandas {pd.__version__}; scikit-learn {sklearn.__version__}")
    print(f"Linhas: {len(data)}; atributos: {X.shape[1]}; ausentes: {int(data.isna().sum().sum())}")
    print(f"Definição positiva: quality >= {POSITIVE_QUALITY_MIN}")
    print(
        "Contagem da classe positiva: "
        f"{int(y.sum())}/{len(y)} ({y.mean():.4%}); classe negativa: {int((1-y).sum())}"
    )
    print(
        "Partições (linhas): "
        f"treino={len(y_train)}; validação={len(y_val)}; teste={len(y_test)}"
    )
    print(
        "Positivos por partição: "
        f"treino={int(y_train.sum())}; validação={int(y_val.sum())}; teste={int(y_test.sum())}"
    )
    print(f"Melhor F1 na validação: {validation_f1:.4f}")
    print("Coeficientes logísticos padronizados (maiores magnitudes, associação condicional):")
    coefficients = model.named_steps["logistic"].coef_[0]
    ranked = sorted(zip(X.columns, coefficients), key=lambda item: abs(item[1]), reverse=True)
    for feature, coefficient in ranked[:5]:
        print(f"  {feature}: {coefficient:+.4f}")

    # O teste final é aberto somente após ajustar e escolher o limiar na validação.
    report_metrics("Teste, limiar padrão 0.50 (referência)", y_test, test_probabilities, 0.50)
    report_metrics(
        "Teste, limiar selecionado pela validação (F1)",
        y_test,
        test_probabilities,
        chosen_threshold,
    )


if __name__ == "__main__":
    main()
