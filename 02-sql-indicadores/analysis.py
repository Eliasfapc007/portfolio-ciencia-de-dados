#!/usr/bin/env python3
"""Métricas SQL de conversão por sessão usando o dataset oficial UCI.

Baixa o CSV público da UCI se necessário, valida o snapshot e calcula métricas
agregadas com SQLite. Os registros individuais permanecem apenas em data/.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import sqlite3
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw"
CSV_PATH = RAW_DIR / "online_shoppers_intention.csv"
ZIP_PATH = RAW_DIR / "online-shoppers-purchasing-intention-dataset.zip"
OUTPUT_DIR = ROOT / "outputs"

DATASET_PAGE = (
    "https://archive.ics.uci.edu/dataset/468/"
    "online+shoppers+purchasing+intention+dataset"
)
DOWNLOAD_URL = (
    "https://archive.ics.uci.edu/static/public/468/"
    "online+shoppers+purchasing+intention+dataset.zip"
)
EXPECTED_CSV_SHA256 = "b3055ee355f59134d851d32641183cb4a8b45def7124d2f50442a042f358e0d9"
EXPECTED_ROWS = 12_330
EXPECTED_BUYING_SESSIONS = 1_908

HEADERS = (
    "Administrative",
    "Administrative_Duration",
    "Informational",
    "Informational_Duration",
    "ProductRelated",
    "ProductRelated_Duration",
    "BounceRates",
    "ExitRates",
    "PageValues",
    "SpecialDay",
    "Month",
    "OperatingSystems",
    "Browser",
    "Region",
    "TrafficType",
    "VisitorType",
    "Weekend",
    "Revenue",
)

INTEGER_COLUMNS = {
    "Administrative",
    "Informational",
    "ProductRelated",
    "OperatingSystems",
    "Browser",
    "Region",
    "TrafficType",
}
FLOAT_COLUMNS = {
    "Administrative_Duration",
    "Informational_Duration",
    "ProductRelated_Duration",
    "BounceRates",
    "ExitRates",
    "PageValues",
    "SpecialDay",
}
MONTH_ORDER = {
    name: index
    for index, name in enumerate(
        ("Jan", "Feb", "Mar", "Apr", "May", "June", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
        start=1,
    )
}
VALID_VISITOR_TYPES = {"Returning_Visitor", "New_Visitor", "Other"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_archive() -> None:
    """Baixa o arquivo público da UCI para um temporário e renomeia atomicamente."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    partial = ZIP_PATH.with_suffix(ZIP_PATH.suffix + ".part")
    request = urllib.request.Request(
        DOWNLOAD_URL,
        headers={"User-Agent": "02-sql-indicadores/1.0 (educational reproducible analysis)"},
    )
    print(f"Baixando o arquivo oficial UCI: {DOWNLOAD_URL}")
    try:
        with urllib.request.urlopen(request, timeout=180) as response, partial.open("wb") as out:
            shutil.copyfileobj(response, out, length=64 * 1024)
        if not zipfile.is_zipfile(partial):
            raise ValueError("A resposta baixada não é um arquivo ZIP válido.")
        partial.replace(ZIP_PATH)
    except Exception:
        partial.unlink(missing_ok=True)
        raise


def ensure_dataset() -> Path:
    """Garante que o CSV local corresponde ao snapshot público esperado."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if CSV_PATH.exists() and sha256_file(CSV_PATH) == EXPECTED_CSV_SHA256:
        return CSV_PATH

    if not ZIP_PATH.exists() or not zipfile.is_zipfile(ZIP_PATH):
        download_archive()

    with zipfile.ZipFile(ZIP_PATH) as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise ValueError(f"Arquivo ZIP corrompido no membro {bad_member!r}.")
        candidates = [name for name in archive.namelist() if Path(name).name == CSV_PATH.name]
        if len(candidates) != 1:
            raise ValueError(
                "O pacote UCI não contém exatamente o CSV esperado "
                f"({CSV_PATH.name!r}); itens encontrados: {candidates}."
            )
        temporary_csv = CSV_PATH.with_suffix(".csv.part")
        try:
            with archive.open(candidates[0]) as source, temporary_csv.open("wb") as target:
                shutil.copyfileobj(source, target, length=64 * 1024)
            actual_hash = sha256_file(temporary_csv)
            if actual_hash != EXPECTED_CSV_SHA256:
                raise ValueError(
                    "O SHA-256 do CSV diverge do snapshot UCI validado. "
                    f"Esperado {EXPECTED_CSV_SHA256}; encontrado {actual_hash}."
                )
            temporary_csv.replace(CSV_PATH)
        except Exception:
            temporary_csv.unlink(missing_ok=True)
            raise
    return CSV_PATH


def parse_int(value: str, field: str, row_number: int) -> int:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Linha {row_number}: {field} não é numérico: {value!r}") from exc
    if not math.isfinite(number) or not number.is_integer():
        raise ValueError(f"Linha {row_number}: {field} deve ser inteiro: {value!r}")
    return int(number)


def parse_float(value: str, field: str, row_number: int) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Linha {row_number}: {field} não é numérico: {value!r}") from exc
    if not math.isfinite(number):
        raise ValueError(f"Linha {row_number}: {field} deve ser finito: {value!r}")
    return number


def make_database(csv_path: Path) -> sqlite3.Connection:
    """Carrega e valida as 18 colunas no SQLite em memória."""
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE sessions (
            row_id INTEGER PRIMARY KEY,
            administrative INTEGER NOT NULL,
            administrative_duration REAL NOT NULL,
            informational INTEGER NOT NULL,
            informational_duration REAL NOT NULL,
            product_related INTEGER NOT NULL,
            product_related_duration REAL NOT NULL,
            bounce_rates REAL NOT NULL,
            exit_rates REAL NOT NULL,
            page_values REAL NOT NULL,
            special_day REAL NOT NULL,
            month TEXT NOT NULL,
            operating_systems INTEGER NOT NULL,
            browser INTEGER NOT NULL,
            region INTEGER NOT NULL,
            traffic_type INTEGER NOT NULL,
            visitor_type TEXT NOT NULL,
            weekend INTEGER NOT NULL CHECK (weekend IN (0, 1)),
            revenue INTEGER NOT NULL CHECK (revenue IN (0, 1))
        )
        """
    )
    placeholders = ",".join("?" for _ in range(18))
    insert_sql = f"INSERT INTO sessions VALUES (NULL, {placeholders})"
    row_count = 0
    buying_count = 0
    batch: list[tuple[Any, ...]] = []

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if tuple(reader.fieldnames or ()) != HEADERS:
            raise ValueError(
                "Cabeçalho inesperado no CSV.\n"
                f"Esperado: {HEADERS}\n"
                f"Recebido: {tuple(reader.fieldnames or ())}"
            )
        for row_number, row in enumerate(reader, start=2):
            if None in row or any(row.get(name) is None or not row[name].strip() for name in HEADERS):
                raise ValueError(f"Linha {row_number}: campos ausentes ou quantidade de colunas inválida.")
            month = row["Month"].strip()
            visitor_type = row["VisitorType"].strip()
            weekend_text = row["Weekend"].strip().upper()
            revenue_text = row["Revenue"].strip().upper()
            if month not in MONTH_ORDER:
                raise ValueError(f"Linha {row_number}: mês inesperado {month!r}.")
            if visitor_type not in VALID_VISITOR_TYPES:
                raise ValueError(f"Linha {row_number}: VisitorType inesperado {visitor_type!r}.")
            if weekend_text not in {"TRUE", "FALSE"} or revenue_text not in {"TRUE", "FALSE"}:
                raise ValueError(f"Linha {row_number}: Weekend/Revenue deve ser TRUE ou FALSE.")

            values: list[Any] = []
            for field in HEADERS:
                if field in INTEGER_COLUMNS:
                    values.append(parse_int(row[field], field, row_number))
                elif field in FLOAT_COLUMNS:
                    values.append(parse_float(row[field], field, row_number))
                elif field == "Month":
                    values.append(month)
                elif field == "VisitorType":
                    values.append(visitor_type)
                elif field == "Weekend":
                    values.append(int(weekend_text == "TRUE"))
                elif field == "Revenue":
                    revenue = int(revenue_text == "TRUE")
                    values.append(revenue)
                    buying_count += revenue
            batch.append(tuple(values))
            row_count += 1
            if len(batch) >= 2_000:
                connection.executemany(insert_sql, batch)
                batch.clear()

    if batch:
        connection.executemany(insert_sql, batch)
    connection.commit()

    if row_count != EXPECTED_ROWS:
        raise ValueError(f"Esperadas {EXPECTED_ROWS:,} linhas; CSV contém {row_count:,}.")
    if buying_count != EXPECTED_BUYING_SESSIONS:
        raise ValueError(
            f"Esperadas {EXPECTED_BUYING_SESSIONS:,} sessões com Revenue=TRUE; "
            f"foram encontradas {buying_count:,}."
        )
    return connection


def records(cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
    return [dict(row) for row in cursor.fetchall()]


def run_queries(connection: sqlite3.Connection) -> dict[str, Any]:
    summary = dict(
        connection.execute(
            """
            SELECT
                COUNT(*) AS sessions,
                SUM(revenue) AS buying_sessions,
                COUNT(*) - SUM(revenue) AS non_buying_sessions,
                ROUND(100.0 * SUM(revenue) / COUNT(*), 4) AS conversion_rate_pct
            FROM sessions
            """
        ).fetchone()
    )
    visitors = records(
        connection.execute(
            """
            SELECT visitor_type,
                   COUNT(*) AS sessions,
                   SUM(revenue) AS buying_sessions,
                   ROUND(100.0 * SUM(revenue) / COUNT(*), 4) AS conversion_rate_pct
            FROM sessions
            GROUP BY visitor_type
            ORDER BY visitor_type
            """
        )
    )
    weekends = records(
        connection.execute(
            """
            SELECT CASE weekend WHEN 1 THEN 'weekend' ELSE 'weekday' END AS day_group,
                   COUNT(*) AS sessions,
                   SUM(revenue) AS buying_sessions,
                   ROUND(100.0 * SUM(revenue) / COUNT(*), 4) AS conversion_rate_pct
            FROM sessions
            GROUP BY weekend
            ORDER BY weekend
            """
        )
    )
    monthly = records(
        connection.execute(
            """
            SELECT month,
                   COUNT(*) AS sessions,
                   SUM(revenue) AS buying_sessions,
                   ROUND(100.0 * SUM(revenue) / COUNT(*), 4) AS conversion_rate_pct
            FROM sessions
            GROUP BY month
            ORDER BY CASE month
                WHEN 'Jan' THEN 1 WHEN 'Feb' THEN 2 WHEN 'Mar' THEN 3
                WHEN 'Apr' THEN 4 WHEN 'May' THEN 5 WHEN 'June' THEN 6
                WHEN 'Jul' THEN 7 WHEN 'Aug' THEN 8 WHEN 'Sep' THEN 9
                WHEN 'Oct' THEN 10 WHEN 'Nov' THEN 11 WHEN 'Dec' THEN 12
            END
            """
        )
    )
    return {
        "source": DATASET_PAGE,
        "csv_sha256": EXPECTED_CSV_SHA256,
        "protocol": {
            "unit_of_analysis": "uma sessão por linha",
            "conversion_definition": "Revenue=TRUE / sessões do grupo * 100",
            "grouping": ["Month", "VisitorType", "Weekend"],
            "engine": "SQLite em memória; métricas calculadas em SQL",
        },
        "overall": summary,
        "by_visitor_type": visitors,
        "by_weekend": weekends,
        "by_month": monthly,
    }


def write_outputs(results: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "summary.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (OUTPUT_DIR / "monthly_conversion.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=("month", "sessions", "buying_sessions", "conversion_rate_pct"),
        )
        writer.writeheader()
        writer.writerows(results["by_month"])
    with (OUTPUT_DIR / "segment_conversion.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=("dimension", "segment", "sessions", "buying_sessions", "conversion_rate_pct"),
        )
        writer.writeheader()
        for row in results["by_visitor_type"]:
            writer.writerow({"dimension": "visitor_type", "segment": row["visitor_type"], **{k: row[k] for k in ("sessions", "buying_sessions", "conversion_rate_pct")}})
        for row in results["by_weekend"]:
            writer.writerow({"dimension": "day_group", "segment": row["day_group"], **{k: row[k] for k in ("sessions", "buying_sessions", "conversion_rate_pct")}})


def main() -> int:
    try:
        csv_path = ensure_dataset()
        digest = sha256_file(csv_path)
        if digest != EXPECTED_CSV_SHA256:
            raise ValueError(f"SHA-256 inesperado para o CSV: {digest}")
        print(f"CSV validado: {csv_path.name} (SHA-256 {digest})")
        connection = make_database(csv_path)
        try:
            results = run_queries(connection)
        finally:
            connection.close()
        write_outputs(results)
        print(f"Sessões: {results['overall']['sessions']:,}")
        print(
            "Conversões: "
            f"{results['overall']['buying_sessions']:,} / {results['overall']['sessions']:,} "
            f"({results['overall']['conversion_rate_pct']:.4f}%)"
        )
        print("Conversão por tipo de visitante:")
        for row in results["by_visitor_type"]:
            print(
                f"  {row['visitor_type']}: {row['buying_sessions']:,}/"
                f"{row['sessions']:,} ({row['conversion_rate_pct']:.4f}%)"
            )
        print("Conversão por mês:")
        for row in results["by_month"]:
            print(
                f"  {row['month']}: {row['buying_sessions']:,}/"
                f"{row['sessions']:,} ({row['conversion_rate_pct']:.4f}%)"
            )
        print(f"Resultados agregados gravados em: {OUTPUT_DIR}")
        return 0
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
