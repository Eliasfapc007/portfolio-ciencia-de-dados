#!/usr/bin/env python3
"""Avalia baselines ingênuo e sazonal na série mensal observada de CO2 do NOAA."""

from __future__ import annotations

import argparse
import math
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from statistics import mean
from typing import Optional


DATA_URL = (
    "https://gml.noaa.gov/aftp/data/trace_gases/co2/in-situ/surface/txt/"
    "co2_mlo_surface-insitu_1_ccgg_MonthlyData.txt"
)
PROJECT_DIR = Path(__file__).resolve().parent
DATA_FILE = PROJECT_DIR / "data" / "raw" / "co2_mlo_surface-insitu_1_ccgg_MonthlyData.txt"
MISSING_VALUE = -999.99
HOLDOUT_MONTHS = 18
SEASONAL_PERIOD = 12


@dataclass(frozen=True)
class Observation:
    month: date
    value_ppm: float


def fetch_data(destination: Path) -> int:
    """Baixa o arquivo oficial e o salva atomicamente no cache local ignorado pelo Git."""
    request = urllib.request.Request(
        DATA_URL,
        headers={"User-Agent": "portfolio-06-series-temporais/1.0 (educational analysis)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            if response.status != 200:
                raise RuntimeError(f"Servidor NOAA respondeu HTTP {response.status}.")
            content = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Não foi possível baixar os dados oficiais: {exc}") from exc

    if len(content) < 1000 or b"dataset_name:" not in content or b"site_code year month" not in content:
        raise RuntimeError("A resposta não parece ser o arquivo mensal esperado do NOAA.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_bytes(content)
    temporary.replace(destination)
    return len(content)


def load_observations(path: Path) -> tuple[list[Observation], int, Optional[str]]:
    """Lê a tabela NOAA, ignorando metadados e sentinelas explícitas de ausência."""
    lines = path.read_text(encoding="utf-8").splitlines()
    header = None
    data_rows = []
    for line in lines:
        columns = line.strip().split()
        if columns[:3] == ["site_code", "year", "month"] and "value" in columns:
            header = columns
            continue
        if header is not None and columns and not line.lstrip().startswith("#"):
            data_rows.append(columns)

    if header is None:
        raise RuntimeError("Não encontrei o cabeçalho 'site_code year month' no arquivo NOAA.")

    column_index = {name: index for index, name in enumerate(header)}
    required = {"year", "month", "value"}
    if not required.issubset(column_index):
        raise RuntimeError(f"Faltam colunas obrigatórias: {sorted(required - set(column_index))}")

    observations = []
    missing_rows = 0
    all_months = []
    for line_number, row in enumerate(data_rows, start=1):
        try:
            year = int(row[column_index["year"]])
            month = int(row[column_index["month"]])
            value = float(row[column_index["value"]])
            observed_month = date(year, month, 1)
        except (IndexError, ValueError) as exc:
            raise RuntimeError(f"Linha de dados {line_number} inválida: {' '.join(row)}") from exc

        all_months.append(observed_month)
        if math.isclose(value, MISSING_VALUE, abs_tol=1e-8):
            missing_rows += 1
            continue
        if not math.isfinite(value):
            raise RuntimeError(f"Valor não finito em {observed_month.isoformat()}.")
        observations.append(Observation(observed_month, value))

    if not observations:
        raise RuntimeError("Nenhuma observação válida foi encontrada.")
    if len(all_months) != len(set(all_months)):
        raise RuntimeError("Há meses duplicados no arquivo; interrompendo para não mascarar problema.")
    if any(current <= previous for previous, current in zip(all_months, all_months[1:])):
        raise RuntimeError("Os registros não estão em ordem estritamente cronológica.")

    version = None
    text = path.read_text(encoding="utf-8")
    citation_match = re.search(r"dataset_citation:.*?Version\s+(\d{4}-\d{2}-\d{2})", text)
    if citation_match:
        version = citation_match.group(1)
    return observations, missing_rows, version


def latest_contiguous_segment(observations: list[Observation]) -> list[Observation]:
    """Retorna o segmento contíguo mais recente, sem preencher meses ausentes."""
    segments: list[list[Observation]] = []
    current = [observations[0]]
    for item in observations[1:]:
        previous = current[-1].month
        expected = date(previous.year + 1, 1, 1) if previous.month == 12 else date(previous.year, previous.month + 1, 1)
        if item.month == expected:
            current.append(item)
        else:
            segments.append(current)
            current = [item]
    segments.append(current)
    return segments[-1]


def mae(actual: list[float], predicted: list[float]) -> float:
    return mean(abs(y - yhat) for y, yhat in zip(actual, predicted))


def rmse(actual: list[float], predicted: list[float]) -> float:
    return math.sqrt(mean((y - yhat) ** 2 for y, yhat in zip(actual, predicted)))


def evaluate(observations: list[Observation], holdout_months: int) -> dict[str, object]:
    segment = latest_contiguous_segment(observations)
    if holdout_months <= 0:
        raise ValueError("O período de teste precisa ser positivo.")
    if len(segment) - holdout_months < SEASONAL_PERIOD:
        raise ValueError(
            f"O segmento mensal contínuo mais recente tem {len(segment)} meses; "
            f"este teste exige {holdout_months + SEASONAL_PERIOD} meses "
            "(histórico sazonal de 12 meses mais holdout). Reduza --holdout-months."
        )

    cutoff = len(segment) - holdout_months
    actual = [item.value_ppm for item in segment[cutoff:]]
    naive_predictions = []
    seasonal_predictions = []

    # Walk-forward de 1 passo: cada previsão para t usa apenas observações anteriores a t.
    # Para meses de teste seguintes, o valor real do mês anterior já estaria disponível.
    for index in range(cutoff, len(segment)):
        naive_predictions.append(segment[index - 1].value_ppm)
        seasonal_predictions.append(segment[index - SEASONAL_PERIOD].value_ppm)

    return {
        "segment_start": segment[0].month,
        "segment_months": len(segment),
        "train_end": segment[cutoff - 1].month,
        "test_start": segment[cutoff].month,
        "test_end": segment[-1].month,
        "n_train": cutoff,
        "n_test": holdout_months,
        "actual": actual,
        "naive_mae": mae(actual, naive_predictions),
        "naive_rmse": rmse(actual, naive_predictions),
        "seasonal_mae": mae(actual, seasonal_predictions),
        "seasonal_rmse": rmse(actual, seasonal_predictions),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compara previsões ingênua e sazonal usando série mensal NOAA sem embaralhar o tempo."
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Usa o arquivo já baixado em data/raw; falha se o cache não existir.",
    )
    parser.add_argument(
        "--holdout-months",
        type=int,
        default=HOLDOUT_MONTHS,
        help=f"Quantidade de meses finais para backtest (padrão: {HOLDOUT_MONTHS}).",
    )
    args = parser.parse_args()

    try:
        if args.offline:
            if not DATA_FILE.exists():
                raise RuntimeError(f"Cache não encontrado: {DATA_FILE}. Execute primeiro sem --offline.")
            download_bytes = DATA_FILE.stat().st_size
            data_action = "cache local (--offline)"
        else:
            download_bytes = fetch_data(DATA_FILE)
            data_action = "download NOAA"

        observations, missing_rows, version = load_observations(DATA_FILE)
        result = evaluate(observations, args.holdout_months)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1

    print("Série temporal mensal de CO2 — NOAA GML / Mauna Loa")
    print(f"Ação de dados: {data_action}; arquivo: {download_bytes:,} bytes")
    if version:
        print(f"Versão indicada no cabeçalho do arquivo: {version}")
    print(
        f"Dados: {len(observations)} observações válidas, de "
        f"{observations[0].month.isoformat()} a {observations[-1].month.isoformat()}; "
        f"{len(observations) + missing_rows} linhas mensais no arquivo e "
        f"{missing_rows} sentinelas de ausência excluídas."
    )
    print(
        f"Protocolo: segmento contínuo mais recente com {result['segment_months']} meses, "
        f"desde {result['segment_start'].isoformat()}; histórico consecutivo até "
        f"{result['train_end'].isoformat()} ({result['n_train']} meses); teste de "
        f"{result['test_start'].isoformat()} a {result['test_end'].isoformat()} "
        f"({result['n_test']} meses), avaliação walk-forward de 1 passo."
    )
    print("Métricas em ppm:")
    print(f"  Ingênuo (último mês): MAE={result['naive_mae']:.4f}; RMSE={result['naive_rmse']:.4f}")
    print(
        f"  Sazonal ingênuo (mesmo mês do ano anterior): "
        f"MAE={result['seasonal_mae']:.4f}; RMSE={result['seasonal_rmse']:.4f}"
    )
    winner = "ingênuo" if result["naive_mae"] < result["seasonal_mae"] else "sazonal ingênuo"
    print(f"Menor MAE neste backtest: {winner}.")
    print("Nota: a comparação é educacional, não uma previsão global nem uma recomendação operacional.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
