"""Data loading utility tests."""

from pathlib import Path

import pandas as pd

from src.data.loaders import (
    find_antidumping_csv,
    load_antidumping_from_raw_dir,
    load_raw_antidumping,
    normalize_unicode_text,
)


def test_normalize_unicode_text_returns_nfc():
    decomposed = "덤핑"
    assert normalize_unicode_text(decomposed) == "덤핑"


def test_find_and_load_raw_antidumping(tmp_path: Path):
    csv_path = tmp_path / "산업통상부_무역구제 덤핑방지 관세 부과 현황_20251231.csv"
    pd.DataFrame(
        {
            "국가명": ["중국"],
            "품목": ["합판"],
            "관세부과범위": ["3.30~27.21"],
            "부과시작일": ["2024-07-02"],
            "부과종료일": ["2029-07-01"],
            "관련법령": ["기획재정부령 제1073호"],
        }
    ).to_csv(csv_path, index=False, encoding="cp949")

    found_path = find_antidumping_csv(tmp_path)
    loaded = load_raw_antidumping(found_path)

    assert found_path == csv_path
    assert loaded.loc[0, "source_row_id"] == 1
    assert loaded.loc[0, "국가명"] == "중국"


def test_load_antidumping_from_raw_dir(tmp_path: Path):
    csv_path = tmp_path / "산업통상부_무역구제 덤핑방지 관세 부과 현황_20251231.csv"
    pd.DataFrame(
        {
            "국가명": ["일본"],
            "품목": ["D.C.P"],
            "관세부과범위": ["가격약속"],
            "부과시작일": ["1989-01-13"],
            "부과종료일": ["1989-12-31"],
            "관련법령": ["재무부 공고 제89-2호"],
        }
    ).to_csv(csv_path, index=False, encoding="cp949")

    found_path, loaded = load_antidumping_from_raw_dir(tmp_path)

    assert found_path == csv_path
    assert loaded.shape == (1, 7)
    assert loaded.loc[0, "품목"] == "D.C.P"
