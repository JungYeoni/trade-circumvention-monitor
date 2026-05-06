"""Reusable data loading utilities."""

from __future__ import annotations

import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

ANTIDUMPING_COLUMNS = ["국가명", "품목", "관세부과범위", "부과시작일", "부과종료일", "관련법령"]


def normalize_unicode_text(value: object) -> str:
    """Normalize text to NFC to avoid macOS Korean filename/string mismatches."""
    return unicodedata.normalize("NFC", str(value))


def find_csv_by_keywords(raw_dir: str | Path, keywords: list[str]) -> Path:
    """Find the CSV file whose filename contains the most requested keywords."""
    raw_path = Path(raw_dir)
    candidates = sorted(raw_path.glob("*.csv"))
    if not candidates:
        raise FileNotFoundError(f"CSV 파일이 없습니다: {raw_path}")

    scored = []
    for path in candidates:
        name = normalize_unicode_text(path.name)
        score = sum(keyword in name for keyword in keywords)
        scored.append((score, path))

    scored.sort(key=lambda item: (-item[0], item[1].name))
    if scored[0][0] == 0:
        raise FileNotFoundError(f"키워드에 맞는 CSV 후보를 찾지 못했습니다: {keywords}")
    return scored[0][1]


def find_antidumping_csv(raw_dir: str | Path) -> Path:
    """Find the anti-dumping duty CSV in a raw data directory."""
    return find_csv_by_keywords(raw_dir, ["덤핑방지", "관세", "부과", "현황"])


def load_raw_antidumping(path: str | Path) -> pd.DataFrame:
    """Load the CP949 anti-dumping raw CSV and add a source row id."""
    df = pd.read_csv(path, encoding="cp949")
    missing = set(ANTIDUMPING_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"필수 컬럼이 없습니다: {sorted(missing)}")

    df = df[ANTIDUMPING_COLUMNS].copy()
    df.insert(0, "source_row_id", np.arange(1, len(df) + 1))
    return df


def load_antidumping_from_raw_dir(raw_dir: str | Path) -> tuple[Path, pd.DataFrame]:
    """Find and load the anti-dumping raw CSV from a raw data directory."""
    path = find_antidumping_csv(raw_dir)
    return path, load_raw_antidumping(path)
