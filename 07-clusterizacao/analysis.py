#!/usr/bin/env python3
"""Segmentação reprodutível do dataset Wholesale customers, da UCI."""

from __future__ import annotations

import argparse
import io
import itertools
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler

PROJECT_DIR = Path(__file__).resolve().parent
CACHE_DIR = PROJECT_DIR / "data"
ZIP_PATH = CACHE_DIR / "wholesale-customers.zip"
DATASET_URL = "https://archive.ics.uci.edu/static/public/292/wholesale+customers.zip"
DATASET_PAGE = "https://archive.ics.uci.edu/dataset/292/wholesale+customers"
SPEND_COLUMNS = [
    "Fresh",
    "Milk",
    "Grocery",
    "Frozen",
    "Detergents_Paper",
    "Delicassen",
]
EXPECTED_COLUMNS = ["Channel", "Region", *SPEND_COLUMNS]
EXPECTED_ROWS = 440
DEFAULT_SEED = 42


def download_archive(refresh: bool = False) -> Path:
    """Obtain the permitted public archive and keep it in ignored local cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if ZIP_PATH.exists() and not refresh:
        return ZIP_PATH

    request = urllib.request.Request(
        DATASET_URL,
        headers={"User-Agent": "portfolio-clustering-analysis/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        archive_bytes = response.read()

    # Validate before replacing the cached file, so a failed download is not cached.
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        csv_members = [
            name
            for name in archive.namelist()
            if name.lower().endswith("wholesale customers data.csv")
        ]
        if len(csv_members) != 1:
            raise ValueError(
                "O arquivo oficial não contém exatamente um CSV esperado; "
                f"conteúdo encontrado: {archive.namelist()}"
            )

    temporary_path = ZIP_PATH.with_suffix(".zip.tmp")
    temporary_path.write_bytes(archive_bytes)
    temporary_path.replace(ZIP_PATH)
    return ZIP_PATH


def load_dataset(refresh: bool = False) -> pd.DataFrame:
    archive_path = download_archive(refresh=refresh)
    with zipfile.ZipFile(archive_path) as archive:
        member = next(
            name
            for name in archive.namelist()
            if name.lower().endswith("wholesale customers data.csv")
        )
        with archive.open(member) as csv_file:
            frame = pd.read_csv(csv_file)

    missing_columns = sorted(set(EXPECTED_COLUMNS) - set(frame.columns))
    unexpected_columns = sorted(set(frame.columns) - set(EXPECTED_COLUMNS))
    if missing_columns or unexpected_columns:
        raise ValueError(
            "Esquema inesperado do CSV oficial. "
            f"Colunas ausentes: {missing_columns}; excedentes: {unexpected_columns}."
        )
    if len(frame) != EXPECTED_ROWS:
        raise ValueError(
            f"Esperadas {EXPECTED_ROWS} linhas conforme a ficha da UCI; "
            f"encontradas {len(frame)}."
        )

    frame[SPEND_COLUMNS] = frame[SPEND_COLUMNS].apply(pd.to_numeric, errors="raise")
    if frame[SPEND_COLUMNS].isna().any().any():
        raise ValueError("Há valores ausentes nas seis variáveis de gastos.")
    if (frame[SPEND_COLUMNS] < 0).any().any():
        raise ValueError("Foram encontrados valores negativos em gastos.")
    return frame


def fit_kmeans(values: np.ndarray, k: int, seed: int) -> KMeans:
    return KMeans(n_clusters=k, random_state=seed, n_init=20).fit(values)


def run_analysis(frame: pd.DataFrame, seed: int) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    # Spending amounts are strongly right-skewed; log1p precedes feature scaling.
    logged = np.log1p(frame[SPEND_COLUMNS].to_numpy(dtype=float))
    scaled = StandardScaler().fit_transform(logged)

    metric_rows: list[dict] = []
    models: dict[int, KMeans] = {}
    for k in range(2, 9):
        model = fit_kmeans(scaled, k, seed)
        labels = model.labels_
        models[k] = model
        metric_rows.append(
            {
                "k": k,
                "inertia": float(model.inertia_),
                "silhouette": float(silhouette_score(scaled, labels)),
                "calinski_harabasz": float(calinski_harabasz_score(scaled, labels)),
                "davies_bouldin": float(davies_bouldin_score(scaled, labels)),
            }
        )

    metrics = pd.DataFrame(metric_rows)
    # Predeclared selection rule: maximize silhouette on the tested k range.
    chosen_k = int(metrics.loc[metrics["silhouette"].idxmax(), "k"])
    chosen_model = models[chosen_k]
    labels = chosen_model.labels_

    # Check sensitivity of the selected partition to KMeans initialization.
    repeated_labels = [
        fit_kmeans(scaled, chosen_k, seed + offset).labels_ for offset in range(10)
    ]
    pairwise_ari = [
        adjusted_rand_score(left, right)
        for left, right in itertools.combinations(repeated_labels, 2)
    ]

    assigned = frame[SPEND_COLUMNS].copy()
    assigned["cluster"] = labels
    profiles = assigned.groupby("cluster")[SPEND_COLUMNS].median()
    sizes = assigned["cluster"].value_counts().sort_index()

    stability = {
        "ari_mean": float(np.mean(pairwise_ari)),
        "ari_min": float(np.min(pairwise_ari)),
        "ari_max": float(np.max(pairwise_ari)),
    }
    results = {"chosen_k": chosen_k, "stability": stability, "sizes": sizes, "seed": seed}
    return metrics, profiles, results


def print_report(frame: pd.DataFrame, metrics: pd.DataFrame, profiles: pd.DataFrame, results: dict) -> None:
    print("Fonte: UCI Machine Learning Repository — Wholesale customers")
    print(f"Página: {DATASET_PAGE}")
    print(f"Arquivo em cache (ignorado pelo Git): {ZIP_PATH.relative_to(PROJECT_DIR)}")
    print(f"Linhas verificadas: {len(frame)}; colunas no CSV: {len(frame.columns)}")
    print(f"Variáveis usadas no agrupamento: {', '.join(SPEND_COLUMNS)}")
    print("Channel e Region foram excluídas do ajuste (categorias, não gastos).")

    print("\nAssimetria de escala nos gastos brutos (máximo / mediana):")
    for column in SPEND_COLUMNS:
        median = float(frame[column].median())
        ratio = float(frame[column].max() / median)
        print(f"  {column}: mediana={median:.1f}; máximo={frame[column].max():.1f}; razão={ratio:.2f}x")

    print("\nPré-processamento: log1p por variável e StandardScaler.")
    print(f"Protocolo: KMeans, n_init=20, random_state={results['seed']}; k testado de 2 a 8.")
    print("Métricas calculadas na matriz log1p padronizada; maior silhouette seleciona k.")
    print("\nMétricas internas:")
    print("k | inertia | silhouette (↑) | Calinski-Harabasz (↑) | Davies-Bouldin (↓)")
    for row in metrics.itertuples(index=False):
        print(
            f"{row.k} | {row.inertia:.3f} | {row.silhouette:.4f} | "
            f"{row.calinski_harabasz:.3f} | {row.davies_bouldin:.4f}"
        )

    chosen_k = results["chosen_k"]
    print(f"\nEscolha pela maior silhouette: k={chosen_k}.")
    stability = results["stability"]
    print(
        "Estabilidade (ARI entre 45 pares de 10 inicializações, k escolhido): "
        f"média={stability['ari_mean']:.4f}; mínimo={stability['ari_min']:.4f}; "
        f"máximo={stability['ari_max']:.4f}."
    )

    print("\nPerfis por cluster — mediana das despesas nas unidades monetárias originais:")
    for cluster in profiles.index:
        count = int(results["sizes"].loc[cluster])
        percentage = count / len(frame) * 100
        spend_text = "; ".join(
            f"{column}={profiles.loc[cluster, column]:.1f}" for column in SPEND_COLUMNS
        )
        print(f"  Cluster {cluster}: n={count} ({percentage:.1f}%); {spend_text}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Agrupa perfis de gastos anuais do dataset real Wholesale customers da UCI."
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="baixar novamente o ZIP oficial em vez de usar o cache local ignorado pelo Git",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="semente do KMeans (padrão: 42)")
    args = parser.parse_args()

    frame = load_dataset(refresh=args.refresh)
    metrics, profiles, results = run_analysis(frame, seed=args.seed)
    print_report(frame, metrics, profiles, results)


if __name__ == "__main__":
    main()
