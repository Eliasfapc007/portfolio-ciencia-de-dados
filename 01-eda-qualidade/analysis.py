#!/usr/bin/env python3
"""EDA de qualidade para o dataset Adult, usando o arquivo ZIP original da UCI."""

from __future__ import annotations

import argparse
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import BinaryIO

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = PROJECT_DIR / "data"
ZIP_URL = "https://archive.ics.uci.edu/static/public/2/adult.zip"
ZIP_FILENAME = "adult.zip"
FILES = {
    "adult.data": 32_561,
    "adult.test": 16_281,
}
COLUMNS = [
    "age",
    "workclass",
    "fnlwgt",
    "education",
    "education-num",
    "marital-status",
    "occupation",
    "relationship",
    "race",
    "sex",
    "capital-gain",
    "capital-loss",
    "hours-per-week",
    "native-country",
    "income",
]
NUMERIC_COLUMNS = [
    "age",
    "fnlwgt",
    "education-num",
    "capital-gain",
    "capital-loss",
    "hours-per-week",
]
VALID_INCOME_LABELS = {"<=50K", ">50K"}


def download_file(url: str, destination: Path, force: bool = False) -> None:
    """Baixa do endpoint oficial UCI; mantém apenas um cache ZIP não versionado."""
    if destination.is_file() and destination.stat().st_size > 0 and not force:
        print(f"Cache local: {destination.name}")
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "01-eda-qualidade/1.0 (reproducible educational analysis)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            with temporary.open("wb") as output:
                shutil.copyfileobj(response, output)
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise RuntimeError(f"O download de {url} retornou um arquivo vazio.")
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    print(f"Baixado: {destination.name} ({destination.stat().st_size:,} bytes)")


def load_part(stream: BinaryIO, filename: str, expected_rows: int) -> pd.DataFrame:
    """Lê parte sem cabeçalho; descarta comentário do teste e normaliza rótulo."""
    frame = pd.read_csv(
        stream,
        sep=",",
        header=None,
        names=COLUMNS,
        skipinitialspace=True,
        comment="|",
        dtype="string",
        na_values=["?"],
        keep_default_na=False,
        on_bad_lines="error",
        encoding="utf-8",
    )
    if list(frame.columns) != COLUMNS:
        raise ValueError(f"{filename}: esquema inesperado.")
    if len(frame) != expected_rows:
        raise ValueError(
            f"{filename}: esperadas {expected_rows:,} linhas de dados, encontradas {len(frame):,}. "
            "Confira o arquivo oficial ou remova o cache ZIP para baixá-lo novamente."
        )

    for column in NUMERIC_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    # O arquivo de teste acrescenta um ponto ao rótulo; remove apenas esse sufixo.
    frame["income"] = frame["income"].str.strip().str.rstrip(".").str.strip()
    return frame


def load_dataset(data_dir: Path, force_download: bool = False) -> pd.DataFrame:
    zip_path = data_dir / ZIP_FILENAME
    download_file(ZIP_URL, zip_path, force=force_download)

    parts: list[pd.DataFrame] = []
    with zipfile.ZipFile(zip_path) as archive:
        corrupt_member = archive.testzip()
        if corrupt_member is not None:
            raise ValueError(f"O ZIP oficial está corrompido no membro {corrupt_member!r}.")
        members = set(archive.namelist())
        missing_files = set(FILES) - members
        if missing_files:
            raise ValueError(f"O ZIP não contém os arquivos esperados: {sorted(missing_files)}")
        for filename, expected_rows in FILES.items():
            with archive.open(filename) as stream:
                parts.append(load_part(stream, filename, expected_rows))

    dataset = pd.concat(parts, ignore_index=True)
    validate_dataset(dataset)
    return dataset


def validate_dataset(data: pd.DataFrame) -> None:
    expected_rows = sum(FILES.values())
    if len(data) != expected_rows:
        raise ValueError(f"Esperadas {expected_rows:,} linhas; encontradas {len(data):,}.")
    if set(data["income"].dropna().unique()) != VALID_INCOME_LABELS:
        raise ValueError("Rótulos inesperados na coluna income após a normalização.")
    if data["income"].isna().any():
        raise ValueError("O rótulo income contém valores ausentes.")

    checks = {
        "age > 16": (data["age"] > 16).all(),
        "fnlwgt > 0": (data["fnlwgt"] > 0).all(),
        "education-num entre 1 e 16": data["education-num"].between(1, 16).all(),
        "capital-gain >= 0": (data["capital-gain"] >= 0).all(),
        "capital-loss >= 0": (data["capital-loss"] >= 0).all(),
        "hours-per-week > 0": (data["hours-per-week"] > 0).all(),
    }
    failed = [description for description, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Validações de domínio falharam: " + "; ".join(failed))


def fmt_int(value: int | float) -> str:
    return f"{int(value):,}".replace(",", ".")


def fmt_pct(value: float) -> str:
    return f"{value:.2f}".replace(".", ",") + "%"


def fmt_decimal(value: float) -> str:
    return f"{value:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


def print_report(data: pd.DataFrame) -> None:
    n_rows = len(data)
    feature_count = len(COLUMNS) - 1
    duplicates = int(data[COLUMNS].duplicated().sum())
    missing_by_column = data[COLUMNS].isna().sum()
    missing_cells = int(missing_by_column.sum())

    print("\n=== Auditoria de qualidade e EDA: UCI Adult ===")
    print(f"Linhas analisadas: {fmt_int(n_rows)}")
    print(f"Colunas: {feature_count} atributos + 1 rótulo")
    print(
        "Partições lidas: "
        + ", ".join(
            f"{filename} {fmt_int(expected_rows)} linhas"
            for filename, expected_rows in FILES.items()
        )
    )
    print(f"Duplicatas exatas entre os campos originais: {fmt_int(duplicates)}")
    print(f"Células ausentes após converter '?' em nulo: {fmt_int(missing_cells)}")
    print("Campos com ausências:")
    if missing_cells == 0:
        print("  nenhuma")
    else:
        for column, count in missing_by_column[missing_by_column > 0].items():
            pct = 100 * count / n_rows
            print(f"  {column}: {fmt_int(count)} ({fmt_pct(pct)})")

    income_counts = data["income"].value_counts().reindex(["<=50K", ">50K"], fill_value=0)
    print("\nDistribuição do rótulo income:")
    for label, count in income_counts.items():
        print(f"  {label}: {fmt_int(count)} ({fmt_pct(100 * count / n_rows)})")

    age = data["age"]
    print("\nDistribuição de age (anos, resumo descritivo):")
    print(
        "  mínimo={}; mediana={}; média={}; máximo={}".format(
            fmt_int(age.min()),
            fmt_decimal(age.median()),
            fmt_decimal(age.mean()),
            fmt_int(age.max()),
        )
    )

    # Agrupamento descritivo dos códigos de escolaridade; não estima efeito causal.
    bins = [0, 8, 12, 16]
    labels = ["1–8", "9–12", "13–16"]
    groups = pd.cut(data["education-num"], bins=bins, labels=labels, include_lowest=True)
    tab = pd.DataFrame(
        {
            "faixa": groups,
            "income_acima_50k": data["income"].eq(">50K").astype("int64"),
        }
    ).groupby("faixa", observed=False).agg(
        n=("income_acima_50k", "size"),
        acima_50k=("income_acima_50k", "sum"),
    )
    tab["percentual"] = 100 * tab["acima_50k"] / tab["n"]
    print("\nPergunta descritiva: qual a fração de income >50K por faixa de education-num?")
    print("  education-num | n | income >50K | taxa bruta")
    for faixa, row in tab.iterrows():
        print(
            f"  {faixa!s:14} | {fmt_int(row['n'])} | "
            f"{fmt_int(row['acima_50k'])} | {fmt_pct(row['percentual'])}"
        )

    print("\nValidações: linhas e esquema de cada arquivo; rótulos; domínio dos campos numéricos.")
    print("Resultado: todas as validações passaram.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Baixa e executa a EDA reproduzível da base UCI Adult."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Pasta de cache local (padrão: ./data; não versionada).",
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Baixa novamente o ZIP original da UCI.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        dataset = load_dataset(args.data_dir.expanduser(), force_download=args.force_download)
    except Exception as exc:  # mensagem útil para erros de rede, parsing ou validação
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    print_report(dataset)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
