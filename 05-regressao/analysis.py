#!/usr/bin/env python3
"""Prediz resistência à compressão do concreto usando o dataset oficial da UCI.

O arquivo original é baixado sob demanda para data/ (ignorada pelo Git).
Nenhum dado é simulado ou incluído no repositório.
"""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
DATA_PATH = DATA_DIR / "Concrete_Data.xls"
DATA_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/"
    "concrete/compressive/Concrete_Data.xls"
)
RANDOM_STATE = 42

FEATURE_COLUMNS = [
    "Cement (component 1)(kg in a m^3 mixture)",
    "Blast Furnace Slag (component 2)(kg in a m^3 mixture)",
    "Fly Ash (component 3)(kg in a m^3 mixture)",
    "Water (component 4)(kg in a m^3 mixture)",
    "Superplasticizer (component 5)(kg in a m^3 mixture)",
    "Coarse Aggregate (component 6)(kg in a m^3 mixture)",
    "Fine Aggregate (component 7)(kg in a m^3 mixture)",
    "Age (day)",
]
TARGET_COLUMN = "Concrete compressive strength(MPa, megapascals)"
FEATURE_LABELS = {
    FEATURE_COLUMNS[0]: "Cimento",
    FEATURE_COLUMNS[1]: "Escória de alto-forno",
    FEATURE_COLUMNS[2]: "Cinza volante",
    FEATURE_COLUMNS[3]: "Água",
    FEATURE_COLUMNS[4]: "Superplastificante",
    FEATURE_COLUMNS[5]: "Agregado graúdo",
    FEATURE_COLUMNS[6]: "Agregado miúdo",
    FEATURE_COLUMNS[7]: "Idade do concreto (dias)",
}


def download_dataset() -> tuple[Path, bool]:
    """Retorna o XLS local; baixa do endereço oficial se ainda não estiver em cache."""
    if DATA_PATH.exists() and DATA_PATH.stat().st_size > 0:
        return DATA_PATH, False

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    partial_path = DATA_PATH.with_suffix(DATA_PATH.suffix + ".part")
    request = urllib.request.Request(
        DATA_URL,
        headers={"User-Agent": "05-regressao-portfolio/1.0 (dataset access)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = response.read()
    except Exception as exc:
        raise RuntimeError(
            "Não foi possível baixar o arquivo XLS oficial da UCI. "
            f"Verifique a conexão e tente novamente: {DATA_URL}"
        ) from exc

    # O arquivo .xls usa o cabeçalho binário OLE Compound File.
    if not payload.startswith(bytes.fromhex("D0CF11E0A1B11AE1")):
        raise RuntimeError(
            "A resposta do endereço oficial não parece ser o arquivo XLS esperado. "
            "O arquivo não foi salvo como dataset."
        )
    partial_path.write_bytes(payload)
    partial_path.replace(DATA_PATH)
    return DATA_PATH, True


def load_dataset(path: Path) -> pd.DataFrame:
    """Lê e valida o esquema esperado do arquivo disponibilizado pela UCI."""
    # Normaliza espaços, preservando o conteúdo dos nomes das colunas.
    frame = pd.read_excel(path, engine="calamine")
    frame.columns = [re.sub(r"\s+", " ", str(name)).strip() for name in frame.columns]

    expected_columns = FEATURE_COLUMNS + [TARGET_COLUMN]
    if list(frame.columns) != expected_columns:
        raise ValueError(
            "O esquema do arquivo mudou. Colunas encontradas: "
            f"{list(frame.columns)!r}"
        )
    if frame.shape != (1030, 9):
        raise ValueError(
            f"Esperadas 1030 linhas e 9 colunas conforme a ficha UCI; "
            f"recebidas {frame.shape[0]} linhas e {frame.shape[1]} colunas."
        )
    if frame.isna().any().any():
        raise ValueError("O arquivo contém valores ausentes; interrompendo a análise.")
    if not np.isfinite(frame.to_numpy(dtype=float)).all():
        raise ValueError("O arquivo contém valores não finitos; interrompendo a análise.")
    return frame


def main() -> None:
    path, downloaded_now = download_dataset()
    data = load_dataset(path)
    X = data[FEATURE_COLUMNS]
    y = data[TARGET_COLUMN]

    # Evita que a mesma combinação de insumos e idade apareça em treino e teste.
    # O teste representa combinações de entrada não vistas, não linhas aleatórias.
    groups = pd.factorize(pd.MultiIndex.from_frame(X))[0]
    splitter = GroupShuffleSplit(
        n_splits=1, test_size=0.20, random_state=RANDOM_STATE
    )
    train_idx, test_idx = next(splitter.split(X, y, groups=groups))
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    train_groups, test_groups = set(groups[train_idx]), set(groups[test_idx])
    if not train_groups.isdisjoint(test_groups):
        raise RuntimeError("Uma combinação de entrada foi dividida entre treino e teste.")

    models = {
        "Baseline (média do treino)": DummyRegressor(strategy="mean"),
        "Regressão linear": LinearRegression(),
        "Random forest": RandomForestRegressor(
            n_estimators=500,
            min_samples_leaf=2,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
    }
    predictions: dict[str, np.ndarray] = {}
    print("Dataset: UCI Concrete Compressive Strength")
    print(f"URL do arquivo: {DATA_URL}")
    print(f"Download nesta execução: {'sim' if downloaded_now else 'não (cache local)'}")
    print(f"Arquivo: {path.stat().st_size} bytes")
    print(f"Observações: {len(data)}; entradas: {X.shape[1]}; alvo: resistência (MPa)")
    print(f"Valores ausentes: {int(data.isna().sum().sum())}")
    print(f"Linhas completas repetidas (além da primeira): {int(data.duplicated().sum())}")
    print(f"Entradas repetidas (além da primeira): {int(X.duplicated().sum())}")
    print(
        "Split agrupado por combinação de entradas: "
        f"treino={len(train_idx)} ({len(train_groups)} grupos), "
        f"teste={len(test_idx)} ({len(test_groups)} grupos), "
        f"random_state={RANDOM_STATE}; grupos em comum=0"
    )
    print("\nMétricas no conjunto de teste (resistência em MPa):")
    print("Modelo | MAE | RMSE | R²")

    for name, model in models.items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        predictions[name] = pred
        mae = mean_absolute_error(y_test, pred)
        rmse = mean_squared_error(y_test, pred) ** 0.5
        r2 = r2_score(y_test, pred)
        print(f"{name} | {mae:.3f} | {rmse:.3f} | {r2:.3f}")

    rf = models["Random forest"]
    rf_pred = predictions["Random forest"]
    residuals = y_test.to_numpy() - rf_pred
    residual_prediction_corr = float(np.corrcoef(rf_pred, residuals)[0, 1])
    print("\nDiagnóstico dos resíduos do random forest (observado - previsto):")
    print(f"Média: {residuals.mean():.3f} MPa")
    print(f"Mediana: {np.median(residuals):.3f} MPa")
    print(f"Desvio-padrão: {residuals.std(ddof=1):.3f} MPa")
    print(f"Quantis 5% e 95%: {np.quantile(residuals, [0.05, 0.95])[0]:.3f}, "
          f"{np.quantile(residuals, [0.05, 0.95])[1]:.3f} MPa")
    print(f"Resíduos positivos (subestimação): {(residuals > 0).mean():.1%}")
    print(f"Correlação de Pearson entre previsto e resíduo: {residual_prediction_corr:.3f}")

    importance = permutation_importance(
        rf,
        X_test,
        y_test,
        scoring="neg_mean_absolute_error",
        n_repeats=20,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    order = np.argsort(importance.importances_mean)[::-1]
    print("\nImportância por permutação no teste (aumento médio do MAE em MPa):")
    for index in order:
        label = FEATURE_LABELS[FEATURE_COLUMNS[index]]
        mean = importance.importances_mean[index]
        std = importance.importances_std[index]
        print(f"{label}: {mean:.3f} ± {std:.3f}")


if __name__ == "__main__":
    main()
