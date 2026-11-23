#!/usr/bin/env python3
"""Compara o comprimento odontoblástico por suplemento em cada dose.

Baixa a representação oficial de ToothGrowth do repositório de código-fonte
R. Nenhuma observação é simulada ou incorporada neste projeto.
"""
from __future__ import annotations

import math
import re
import sys
from collections import Counter
from pathlib import Path
from statistics import mean, variance
from urllib.error import URLError
from urllib.request import Request, urlopen

from scipy import stats

PROJECT_DIR = Path(__file__).resolve().parent
RAW_PATH = PROJECT_DIR / "data" / "raw" / "ToothGrowth.R"
SOURCE_URL = "https://svn.r-project.org/R/trunk/src/library/datasets/data/ToothGrowth.R"
EXPECTED_N = 60
EXPECTED_DOSES = (0.5, 1.0, 2.0)
EXPECTED_SUPPLEMENTS = ("OJ", "VC")
ALPHA = 0.05


def download_source() -> str:
    """Fetch the official source file, falling back only to a prior real download."""
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    request = Request(SOURCE_URL, headers={"User-Agent": "03-inferencia-experimento/1.0"})
    try:
        with urlopen(request, timeout=30) as response:
            content_type = response.headers.get("Content-Type", "")
            payload = response.read()
        source = payload.decode("utf-8")
        if "text/html" in content_type.lower() or "ToothGrowth <-" not in source:
            raise ValueError("A resposta da fonte não parece ser o arquivo R esperado.")
        RAW_PATH.write_text(source, encoding="utf-8")
        print(f"Fonte baixada: {SOURCE_URL}")
        return source
    except (URLError, TimeoutError, OSError) as exc:
        if not RAW_PATH.exists():
            raise RuntimeError(
                "Não foi possível baixar o arquivo-fonte oficial e não há cópia local. "
                "Verifique a conexão e execute novamente."
            ) from exc
        print(
            f"Aviso: download falhou ({exc}); usando a cópia previamente baixada em "
            f"{RAW_PATH.relative_to(PROJECT_DIR)}.",
            file=sys.stderr,
        )
        return RAW_PATH.read_text(encoding="utf-8")


def capture(pattern: str, source: str, field: str) -> str:
    match = re.search(pattern, source, flags=re.DOTALL)
    if match is None:
        raise ValueError(f"Não foi possível interpretar o campo {field} na fonte oficial.")
    return match.group(1)


def parse_numeric_vector(block: str, field: str) -> list[float]:
    try:
        values = [float(token.strip()) for token in block.split(",")]
    except ValueError as exc:
        raise ValueError(f"Valor não numérico no vetor {field}.") from exc
    if not values or not all(math.isfinite(value) for value in values):
        raise ValueError(f"Vetor {field} vazio ou com valor não finito.")
    return values


def parse_dataset(source: str) -> list[dict[str, float | str]]:
    len_block = capture(r"\blen\s*=\s*c\((.*?)\)\s*,\s*supp\s*=", source, "len")
    len_values = parse_numeric_vector(len_block, "len")

    supp_match = re.search(
        r'\bsupp\s*=\s*factor\s*\(\s*c\((.*?)\)\s*,\s*'
        r'levels\s*=\s*1\s*:\s*2\s*,\s*labels\s*=\s*c\(\s*'
        r'"([^"]+)"\s*,\s*"([^"]+)"\s*\)\s*\)',
        source,
        flags=re.DOTALL,
    )
    if supp_match is None:
        raise ValueError("Não foi possível interpretar o fator supp e seus rótulos.")
    code_values = parse_numeric_vector(supp_match.group(1), "supp")
    labels = (supp_match.group(2), supp_match.group(3))
    if labels != EXPECTED_SUPPLEMENTS:
        raise ValueError(f"Rótulos inesperados em supp: {labels!r}.")
    if any(code not in (1.0, 2.0) for code in code_values):
        raise ValueError("O fator supp contém código diferente dos níveis documentados 1 e 2.")
    supplement_values = [labels[int(code) - 1] for code in code_values]

    dose_block = capture(r"\bdose\s*=\s*c\((.*?)\)\s*\)\s*$", source, "dose")
    dose_values = parse_numeric_vector(dose_block, "dose")

    lengths = {len(len_values), len(supplement_values), len(dose_values)}
    if lengths != {EXPECTED_N}:
        raise ValueError(
            "Número de observações inconsistente; esperava-se 60 valores em cada vetor, "
            f"mas foram encontrados {len(len_values)}, "
            f"{len(supplement_values)} e {len(dose_values)}."
        )
    if set(dose_values) != set(EXPECTED_DOSES):
        raise ValueError(f"Níveis de dose inesperados: {sorted(set(dose_values))!r}.")

    rows = [
        {"len": length, "supp": supplement, "dose": dose}
        for length, supplement, dose in zip(len_values, supplement_values, dose_values)
    ]
    counts = Counter((row["dose"], row["supp"]) for row in rows)
    expected_cells = {(dose, supp) for dose in EXPECTED_DOSES for supp in EXPECTED_SUPPLEMENTS}
    if set(counts) != expected_cells or any(counts[cell] != 10 for cell in expected_cells):
        raise ValueError("Balanceamento inesperado: cada combinação dose × suplemento deve ter n=10.")
    return rows


def holm_adjust(p_values: list[float]) -> list[float]:
    """Holm step-down adjusted p-values, in the original comparison order."""
    order = sorted(range(len(p_values)), key=p_values.__getitem__)
    adjusted = [0.0] * len(p_values)
    running_max = 0.0
    for rank, index in enumerate(order):
        candidate = min(1.0, (len(p_values) - rank) * p_values[index])
        running_max = max(running_max, candidate)
        adjusted[index] = running_max
    return adjusted


def analyze(rows: list[dict[str, float | str]]) -> list[dict[str, float | int | str]]:
    comparisons: list[dict[str, float | int | str]] = []
    n_tests = len(EXPECTED_DOSES)
    ci_confidence = 1.0 - ALPHA / n_tests
    critical_value_probability = 1.0 - ALPHA / (2.0 * n_tests)

    for dose in EXPECTED_DOSES:
        oj = [float(row["len"]) for row in rows if row["dose"] == dose and row["supp"] == "OJ"]
        vc = [float(row["len"]) for row in rows if row["dose"] == dose and row["supp"] == "VC"]
        if len(oj) < 2 or len(vc) < 2:
            raise ValueError(f"Amostra insuficiente para o teste na dose {dose:g}.")

        result = stats.ttest_ind(oj, vc, equal_var=False, alternative="two-sided")
        var_oj = variance(oj)
        var_vc = variance(vc)
        se_squared = var_oj / len(oj) + var_vc / len(vc)
        standard_error = math.sqrt(se_squared)
        df = se_squared**2 / (
            (var_oj / len(oj)) ** 2 / (len(oj) - 1)
            + (var_vc / len(vc)) ** 2 / (len(vc) - 1)
        )
        difference = mean(oj) - mean(vc)
        critical = float(stats.t.ppf(critical_value_probability, df))
        comparisons.append(
            {
                "dose": dose,
                "n_oj": len(oj),
                "n_vc": len(vc),
                "mean_oj": mean(oj),
                "mean_vc": mean(vc),
                "difference": difference,
                "t": float(result.statistic),
                "df": df,
                "p_raw": float(result.pvalue),
                "ci_low": difference - critical * standard_error,
                "ci_high": difference + critical * standard_error,
                "ci_confidence": ci_confidence,
            }
        )

    adjusted = holm_adjust([float(item["p_raw"]) for item in comparisons])
    for item, p_adjusted in zip(comparisons, adjusted):
        item["p_holm"] = p_adjusted
    return comparisons


def main() -> None:
    rows = parse_dataset(download_source())
    comparisons = analyze(rows)
    print(f"Observações validadas: {len(rows)}")
    print("Protocolo: t de Welch bilateral, contrastes OJ − VC dentro de cada dose.")
    print(
        "Família de 3 testes; alfa=0,05; p ajustado por Holm e "
        "intervalos simultâneos Bonferroni de 98,33%."
    )
    print("Diferença positiva indica média amostral maior em OJ; unidade de len não informada.")
    for item in comparisons:
        decision = "rejeita H0" if float(item["p_holm"]) < ALPHA else "não rejeita H0"
        print(
            f"Dose {float(item['dose']):g} mg/dia | n OJ={item['n_oj']}, VC={item['n_vc']} | "
            f"médias OJ={float(item['mean_oj']):.3f}, VC={float(item['mean_vc']):.3f} | "
            f"diferença={float(item['difference']):.3f} | "
            f"IC simultâneo=[{float(item['ci_low']):.3f}, {float(item['ci_high']):.3f}] | "
            f"t({float(item['df']):.2f})={float(item['t']):.3f} | "
            f"p={float(item['p_raw']):.6f}, p_Holm={float(item['p_holm']):.6f} | "
            f"decisão={decision}"
        )
    print("Limite de interpretação: contraste de médias observadas; não infere causalidade.")


if __name__ == "__main__":
    main()
