#!/usr/bin/env python3
"""Compare popularity and item-item collaborative filtering on MovieLens latest-small."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import math
import sys
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy import sparse

DATA_URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
EXPECTED_RATING_COLUMNS = {"userId", "movieId", "rating", "timestamp"}
EXPECTED_MOVIE_COLUMNS = {"movieId", "title", "genres"}


def ensure_archive(data_dir: Path, refresh: bool = False) -> Path:
    data_dir.mkdir(parents=True, exist_ok=True)
    archive_path = data_dir / "ml-latest-small.zip"
    if archive_path.exists() and not refresh:
        return archive_path

    temp_path = archive_path.with_suffix(".zip.part")
    request = urllib.request.Request(
        DATA_URL, headers={"User-Agent": "portfolio-09-recommendation/1.0"}
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response, temp_path.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)
        if temp_path.stat().st_size == 0:
            raise RuntimeError("O arquivo baixado está vazio.")
        temp_path.replace(archive_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    return archive_path


def member_by_basename(archive: zipfile.ZipFile, basename: str) -> str:
    matches = [name for name in archive.namelist() if name.rsplit("/", 1)[-1] == basename]
    if len(matches) != 1:
        raise ValueError(f"Esperava exatamente um {basename} no ZIP; encontrei {len(matches)}.")
    return matches[0]


def read_csv_member(archive: zipfile.ZipFile, member: str) -> csv.DictReader:
    """Return a DictReader backed by the ZIP member's decoded stream."""
    binary = archive.open(member, "r")
    text = io.TextIOWrapper(binary, encoding="utf-8", newline="")
    return csv.DictReader(text)


def load_dataset(archive_path: Path) -> tuple[list[tuple[int, int, float, int]], int]:
    with zipfile.ZipFile(archive_path) as archive:
        rating_reader = read_csv_member(archive, member_by_basename(archive, "ratings.csv"))
        if set(rating_reader.fieldnames or []) != EXPECTED_RATING_COLUMNS:
            raise ValueError(f"Cabeçalho inesperado em ratings.csv: {rating_reader.fieldnames}")
        ratings: list[tuple[int, int, float, int]] = []
        seen_pairs: set[tuple[int, int]] = set()
        for line_number, row in enumerate(rating_reader, start=2):
            try:
                user_id = int(row["userId"])
                movie_id = int(row["movieId"])
                rating = float(row["rating"])
                timestamp = int(row["timestamp"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Linha inválida em ratings.csv:{line_number}") from exc
            if not (0.5 <= rating <= 5.0) or not math.isclose(rating * 2, round(rating * 2)):
                raise ValueError(f"Avaliação fora da escala de meia estrela na linha {line_number}.")
            if timestamp < 0:
                raise ValueError(f"Timestamp negativo na linha {line_number}.")
            pair = (user_id, movie_id)
            if pair in seen_pairs:
                raise ValueError(f"Interação userId/movieId duplicada: {pair}.")
            seen_pairs.add(pair)
            ratings.append((user_id, movie_id, rating, timestamp))

        movie_reader = read_csv_member(archive, member_by_basename(archive, "movies.csv"))
        if set(movie_reader.fieldnames or []) != EXPECTED_MOVIE_COLUMNS:
            raise ValueError(f"Cabeçalho inesperado em movies.csv: {movie_reader.fieldnames}")
        movie_ids: set[int] = set()
        for line_number, row in enumerate(movie_reader, start=2):
            try:
                movie_ids.add(int(row["movieId"]))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Linha inválida em movies.csv:{line_number}") from exc
    if not ratings:
        raise ValueError("ratings.csv não contém avaliações.")
    if not set(movie_id for _, movie_id, _, _ in ratings).issubset(movie_ids):
        raise ValueError("Há movieId em ratings.csv ausente do catálogo movies.csv.")
    return ratings, len(movie_ids)


def chronological_split(
    ratings: Iterable[tuple[int, int, float, int]], train_fraction: float = 0.8
) -> tuple[list[tuple[int, int, float, int]], list[tuple[int, int, float, int]]]:
    """Split each user's events by timestamp, keeping equal-time events together."""
    by_user: dict[int, list[tuple[int, int, float, int]]] = defaultdict(list)
    for event in ratings:
        by_user[event[0]].append(event)

    train: list[tuple[int, int, float, int]] = []
    test: list[tuple[int, int, float, int]] = []
    for user_id in sorted(by_user):
        events = sorted(by_user[user_id], key=lambda event: (event[3], event[1]))
        if len(events) < 2:
            continue
        target_train_count = max(1, min(len(events) - 1, int(len(events) * train_fraction)))
        unique_timestamps = sorted({event[3] for event in events})
        cut_candidates = unique_timestamps[1:]
        if not cut_candidates:
            continue
        cutoff = min(
            cut_candidates,
            key=lambda timestamp: (
                abs(sum(event[3] < timestamp for event in events) - target_train_count),
                timestamp,
            ),
        )
        user_train = [event for event in events if event[3] < cutoff]
        user_test = [event for event in events if event[3] >= cutoff]
        if not user_train or not user_test:
            continue
        train.extend(user_train)
        test.extend(user_test)
    if not train or not test:
        raise ValueError("A divisão temporal não produziu conjuntos de treino e teste.")
    return train, test


def rank_top_k(candidate_indices: np.ndarray, scores: np.ndarray, movie_ids: np.ndarray, k: int) -> np.ndarray:
    # Explicit movieId tie-break makes tied scores fully deterministic.
    order = np.lexsort((movie_ids[candidate_indices], -scores[candidate_indices]))
    return candidate_indices[order[:k]]


def score_recommendations(
    train: list[tuple[int, int, float, int]],
    test: list[tuple[int, int, float, int]],
    all_movie_ids: np.ndarray,
    k: int,
) -> dict[str, float | int]:
    user_ids = np.array(sorted({event[0] for event in train}), dtype=np.int64)
    movie_ids = all_movie_ids
    user_index = {user_id: index for index, user_id in enumerate(user_ids.tolist())}
    movie_index = {movie_id: index for index, movie_id in enumerate(movie_ids.tolist())}
    n_users, n_movies = len(user_ids), len(movie_ids)

    train_by_user: dict[int, list[tuple[int, int, float, int]]] = defaultdict(list)
    for event in train:
        train_by_user[event[0]].append(event)
    test_relevant: dict[int, set[int]] = defaultdict(set)
    for user_id, movie_id, rating, _ in test:
        if rating >= 4.0:
            test_relevant[user_id].add(movie_id)

    positive_train = [event for event in train if event[2] >= 4.0]
    positive_counts = np.zeros(n_movies, dtype=np.float64)
    liked_rows: list[int] = []
    liked_cols: list[int] = []
    for user_id, movie_id, _, _ in positive_train:
        liked_rows.append(movie_index[movie_id])
        liked_cols.append(user_index[user_id])
        positive_counts[movie_index[movie_id]] += 1.0

    interactions = sparse.coo_matrix(
        (np.ones(len(liked_rows), dtype=np.float32), (liked_rows, liked_cols)),
        shape=(n_movies, n_users),
        dtype=np.float32,
    ).tocsr()
    cooccurrence = (interactions @ interactions.T).tocsr()
    item_popularity = np.asarray(interactions.sum(axis=1)).ravel()
    inverse_norm = np.zeros_like(item_popularity, dtype=np.float32)
    nonzero = item_popularity > 0
    inverse_norm[nonzero] = 1.0 / np.sqrt(item_popularity[nonzero])
    normalizer = sparse.diags(inverse_norm, format="csr")
    similarity = (normalizer @ cooccurrence @ normalizer).tocsr()
    similarity.setdiag(0)
    similarity.eliminate_zeros()

    movie_ids_by_index = movie_ids
    recall_values = {"popularidade": [], "item_item_cosine": []}
    ndcg_values = {"popularidade": [], "item_item_cosine": []}
    evaluable_users = sorted(user_id for user_id, relevant in test_relevant.items() if relevant)
    if not evaluable_users:
        raise ValueError("Nenhum usuário tem avaliação relevante (>=4) no período de teste.")

    for user_id in evaluable_users:
        relevant = test_relevant[user_id]
        seen_indices = np.array(
            sorted({movie_index[event[1]] for event in train_by_user[user_id]}), dtype=np.int64
        )
        candidate_mask = np.ones(n_movies, dtype=bool)
        candidate_mask[seen_indices] = False
        candidates = np.flatnonzero(candidate_mask)
        if len(candidates) == 0:
            continue

        top_pop = rank_top_k(candidates, positive_counts, movie_ids_by_index, k)
        liked_indices = np.array(
            sorted({movie_index[event[1]] for event in train_by_user[user_id] if event[2] >= 4.0}),
            dtype=np.int64,
        )
        if len(liked_indices):
            item_scores = np.asarray(similarity[:, liked_indices].sum(axis=1)).ravel()
        else:
            item_scores = np.zeros(n_movies, dtype=np.float64)
        top_cf = rank_top_k(candidates, item_scores, movie_ids_by_index, k)

        ideal_hits = min(len(relevant), k)
        ideal_dcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
        for model, top_indices in (("popularidade", top_pop), ("item_item_cosine", top_cf)):
            top_movie_ids = [int(movie_ids_by_index[index]) for index in top_indices]
            hit_ranks = [rank for rank, movie_id in enumerate(top_movie_ids, start=1) if movie_id in relevant]
            recall_values[model].append(len(hit_ranks) / len(relevant))
            dcg = sum(1.0 / math.log2(rank + 1) for rank in hit_ranks)
            ndcg_values[model].append(dcg / ideal_dcg if ideal_dcg else 0.0)

    if not recall_values["popularidade"]:
        raise ValueError("Nenhum usuário foi elegível para avaliação após excluir itens vistos.")
    return {
        "k": k,
        "eligible_users": len(recall_values["popularidade"]),
        "test_relevant_interactions": sum(len(test_relevant[user]) for user in evaluable_users),
        "recall_at_k_popularity": float(np.mean(recall_values["popularidade"])),
        "ndcg_at_k_popularity": float(np.mean(ndcg_values["popularidade"])),
        "recall_at_k_item_item_cosine": float(np.mean(recall_values["item_item_cosine"])),
        "ndcg_at_k_item_item_cosine": float(np.mean(ndcg_values["item_item_cosine"])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "data" / "raw",
        help="Diretório local ignorado pelo Git para o ZIP baixado.",
    )
    parser.add_argument("--refresh", action="store_true", help="Baixa novamente o arquivo oficial.")
    parser.add_argument("--k", type=int, default=10, help="Tamanho da lista recomendada (padrão: 10).")
    args = parser.parse_args()
    if args.k < 1:
        parser.error("--k deve ser pelo menos 1")

    try:
        archive_path = ensure_archive(args.data_dir, refresh=args.refresh)
        ratings, catalog_size = load_dataset(archive_path)
        train, test = chronological_split(ratings)
        rating_movie_ids = np.array(sorted({event[1] for event in ratings}), dtype=np.int64)
        metrics = score_recommendations(train, test, rating_movie_ids, args.k)
        timestamps = [event[3] for event in ratings]
        result = {
            "dataset": "MovieLens latest-small",
            "source_url": DATA_URL,
            "archive_bytes": archive_path.stat().st_size,
            "ratings": len(ratings),
            "users": len({event[0] for event in ratings}),
            "movies_with_ratings": len(rating_movie_ids),
            "movies_in_metadata": catalog_size,
            "rating_min": min(event[2] for event in ratings),
            "rating_max": max(event[2] for event in ratings),
            "timestamp_start_utc": dt.datetime.fromtimestamp(min(timestamps), tz=dt.timezone.utc).date().isoformat(),
            "timestamp_end_utc": dt.datetime.fromtimestamp(max(timestamps), tz=dt.timezone.utc).date().isoformat(),
            "train_interactions": len(train),
            "test_interactions": len(test),
            "temporal_train_fraction_requested": 0.8,
            "positive_rating_threshold": 4.0,
            "metrics": metrics,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    except (OSError, urllib.error.URLError, zipfile.BadZipFile, ValueError, RuntimeError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
