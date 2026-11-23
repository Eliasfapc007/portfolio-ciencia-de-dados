#!/usr/bin/env python3
"""Classificação binária de polaridade em reviews reais do corpus RePro.

O CSV permanece em data/ (ignorado pelo Git); nenhuma linha de texto é exibida
ou exportada. O arquivo-fonte e o commit são fixados para reprodutibilidade.
"""
from __future__ import annotations

import argparse
import ast
import collections
import csv
import hashlib
import json
import platform
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

from sklearn import __version__ as sklearn_version
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
DATA_PATH = DATA_DIR / "RePro.csv"
DATA_URL = (
    "https://huggingface.co/datasets/lucasnil/repro/resolve/"
    "cb93d9cc1183d4a594317a5188d325bcaa04cda4/RePro.csv"
)
LABEL_ORDER = ["NEGATIVO", "POSITIVO"]
VALID_POLARITIES = {"NEGATIVO", "POSITIVO", "NEUTRO"}


def download_dataset(refresh: bool = False) -> Path:
    """Baixa do Hugging Face sem autenticação e mantém cópia local ignorada."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if DATA_PATH.is_file() and DATA_PATH.stat().st_size > 0 and not refresh:
        return DATA_PATH

    temporary_path = DATA_PATH.with_suffix(".csv.part")
    request = urllib.request.Request(
        DATA_URL,
        headers={"User-Agent": "portfolio-08-nlp-texto/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            if response.status != 200:
                raise RuntimeError(f"Download retornou HTTP {response.status}.")
            with temporary_path.open("wb") as destination:
                while chunk := response.read(1024 * 1024):
                    destination.write(chunk)
        if temporary_path.stat().st_size == 0:
            raise RuntimeError("O arquivo baixado está vazio.")
        temporary_path.replace(DATA_PATH)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    return DATA_PATH


def load_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    """Lê CSV UTF-8 e falha claramente diante de esquema/linhas inválidas."""
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError("O CSV não contém cabeçalho.")
        required = {"review_text", "polarity", "submission_date"}
        missing = sorted(required - set(reader.fieldnames))
        if missing:
            raise ValueError(f"Colunas obrigatórias ausentes: {missing}.")
        rows = list(reader)
        expected_fields = len(reader.fieldnames)

    malformed_count = sum(
        None in row or any(value is None for value in row.values())
        or len(row) != expected_fields
        for row in rows
    )
    if malformed_count:
        raise ValueError(
            f"CSV contém {malformed_count} registro(s) com quantidade de campos inválida."
        )
    if not rows:
        raise ValueError("O CSV não contém registros.")
    return rows, reader.fieldnames


def prepare_binary_reviews(
    rows: list[dict[str, str]],
) -> tuple[list[str], list[str], dict[str, int]]:
    """Mantém polaridades unitárias positiva/negativa e remove textos duplicados.

    Reviews com polaridade neutra ou com opiniões mistas não têm alvo binário
    inequívoco e são excluídos. Duplicatas com rótulos conflitantes também são
    removidas integralmente para evitar leakage e arbitrariedade.
    """
    counts: collections.Counter[str] = collections.Counter()
    candidates: list[tuple[str, str]] = []
    date_values: list[datetime] = []

    for row_number, row in enumerate(rows, start=2):
        text = (row.get("review_text") or "").strip()
        raw_polarity = (row.get("polarity") or "").strip()
        if not text:
            counts["empty_text"] += 1
            continue
        try:
            parsed = ast.literal_eval(raw_polarity)
        except (ValueError, SyntaxError):
            counts["invalid_polarity_format"] += 1
            continue
        if not isinstance(parsed, list) or not all(
            isinstance(label, str) and label in VALID_POLARITIES for label in parsed
        ):
            counts["invalid_polarity_value"] += 1
            continue

        labels = list(dict.fromkeys(label.upper() for label in parsed))
        if len(labels) == 1 and labels[0] in LABEL_ORDER:
            candidates.append((text, labels[0]))
            counts[f"{labels[0].lower()}_only"] += 1
        elif labels == ["NEUTRO"]:
            counts["neutral_only"] += 1
        else:
            counts["mixed_or_nonbinary"] += 1

        raw_date = (row.get("submission_date") or "").strip()
        if raw_date:
            try:
                date_values.append(datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S"))
            except ValueError as exc:
                raise ValueError(
                    f"Data inválida no registro CSV {row_number}; esperado YYYY-MM-DD HH:MM:SS."
                ) from exc

    grouped: dict[str, list[str]] = {}
    for text, label in candidates:
        grouped.setdefault(text, []).append(label)

    conflicting_groups = {
        text for text, labels in grouped.items() if len(set(labels)) > 1
    }
    conflict_rows = sum(len(grouped[text]) for text in conflicting_groups)
    duplicate_rows_removed = sum(
        len(labels) - 1
        for text, labels in grouped.items()
        if text not in conflicting_groups
    )

    texts: list[str] = []
    targets: list[str] = []
    for text, labels in grouped.items():
        if text in conflicting_groups:
            continue
        texts.append(text)
        targets.append(labels[0])

    counts["candidate_rows_before_dedup"] = len(candidates)
    counts["unique_candidate_texts"] = len(grouped)
    counts["conflicting_text_groups"] = len(conflicting_groups)
    counts["rows_in_conflicting_groups_excluded"] = conflict_rows
    counts["duplicate_rows_removed"] = duplicate_rows_removed
    counts["usable_after_dedup"] = len(texts)
    counts["dated_records"] = len(date_values)
    if date_values:
        counts["first_submission_yyyymmdd"] = int(min(date_values).strftime("%Y%m%d"))
        counts["last_submission_yyyymmdd"] = int(max(date_values).strftime("%Y%m%d"))
    return texts, targets, dict(counts)


def score_predictions(y_true: list[str], y_pred: list[str]) -> dict[str, object]:
    report = classification_report(
        y_true,
        y_pred,
        labels=LABEL_ORDER,
        output_dict=True,
        zero_division=0,
    )
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=LABEL_ORDER, average="macro")),
        "per_class": {
            label: {
                "precision": float(report[label]["precision"]),
                "recall": float(report[label]["recall"]),
                "f1": float(report[label]["f1-score"]),
                "support": int(report[label]["support"]),
            }
            for label in LABEL_ORDER
        },
        "confusion_matrix": confusion_matrix(
            y_true, y_pred, labels=LABEL_ORDER
        ).tolist(),
        "misclassified": int(sum(actual != predicted for actual, predicted in zip(y_true, y_pred))),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Avalia um classificador TF-IDF no dataset público RePro."
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Baixa novamente a versão do CSV fixada no script.",
    )
    args = parser.parse_args()

    data_path = download_dataset(refresh=args.refresh)
    rows, columns = load_rows(data_path)
    texts, labels, prep_counts = prepare_binary_reviews(rows)

    label_counts = collections.Counter(labels)
    if len(label_counts) != 2 or min(label_counts.values(), default=0) < 2:
        raise ValueError("Após preparação, são necessárias duas classes com ao menos 2 exemplos.")

    x_train, x_test, y_train, y_test = train_test_split(
        texts,
        labels,
        test_size=0.20,
        random_state=42,
        stratify=labels,
    )

    baseline = DummyClassifier(strategy="most_frequent")
    baseline.fit([[0]] * len(y_train), y_train)
    baseline_predictions = baseline.predict([[0]] * len(y_test)).tolist()

    model = Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    min_df=2,
                    max_features=100_000,
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    C=1.0,
                    class_weight="balanced",
                    max_iter=1_000,
                    random_state=42,
                    solver="liblinear",
                ),
            ),
        ]
    )
    model.fit(x_train, y_train)
    model_predictions = model.predict(x_test).tolist()

    sha256 = hashlib.sha256(data_path.read_bytes()).hexdigest()
    output = {
        "dataset": {
            "name": "RePro",
            "source_url": DATA_URL,
            "download_bytes": data_path.stat().st_size,
            "sha256": sha256,
            "raw_rows_observed": len(rows),
            "csv_columns": len(columns),
            "preparation_counts": prep_counts,
            "usable_class_counts": dict(sorted(label_counts.items())),
        },
        "protocol": {
            "split": "train/test estratificado",
            "test_size": 0.20,
            "random_state": 42,
            "n_train": len(y_train),
            "n_test": len(y_test),
            "class_order_confusion_matrix": LABEL_ORDER,
            "tfidf": {
                "word_ngrams": [1, 2],
                "min_df": 2,
                "max_features": 100_000,
                "sublinear_tf": True,
            },
            "classifier": "LogisticRegression(C=1.0, class_weight='balanced', solver='liblinear')",
            "python": platform.python_version(),
            "scikit_learn": sklearn_version,
        },
        "baseline_majority": score_predictions(y_test, baseline_predictions),
        "tfidf_logistic_regression": score_predictions(y_test, model_predictions),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
