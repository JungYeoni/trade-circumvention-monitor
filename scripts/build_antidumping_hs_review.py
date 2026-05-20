from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INTERIM_DIR = PROJECT_ROOT / "data" / "interim"
REPORTS_DIR = PROJECT_ROOT / "reports"

HISTORY_PATH = INTERIM_DIR / "반덤핑_HS코드_이력.csv"
EVENTS_PATH = INTERIM_DIR / "regulation_events.csv"
REVIEW_PATH = INTERIM_DIR / "반덤핑_HS코드_검토목록.csv"
REPORT_PATH = REPORTS_DIR / "08_antidumping_hs_mapping_status.md"

HS_COLUMNS = ["HS1992", "HS1996", "HS2002", "HS2007", "HS2012", "HS2017", "HS2022"]

# hs_version 값 → HS_COLUMNS 이름 매핑
HS_VERSION_TO_COL = {
    "HS1992": "HS1992",
    "HS1996": "HS1996",
    "HS2002": "HS2002",
    "HS2007": "HS2007",
    "HS2012": "HS2012",
    "HS2017": "HS2017",
    "HS2022": "HS2022",
}


def _read_csv(path: Path) -> pd.DataFrame:
    """CSV 파일을 모든 컬럼을 str로 읽어 반환한다."""
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def _clean_hs_code(value: str) -> str:
    """HS 코드 문자열에서 공백·소수점 접미사를 제거해 정규화한다."""
    value = value.strip()
    if value.endswith(".0"):
        value = value[:-2]
    return value.replace(".", "")


def _pivot_long_to_wide(history: pd.DataFrame) -> pd.DataFrame:
    """long-format 이력 테이블(품목×개정판)을 wide-format(품목 1행)으로 변환한다.

    입력 컬럼: 품목명_정규화, 품목명_원문예시, hs_version, hs_code, mapping_status, note 등
    출력 컬럼: 품목명_정규화, 품목명_원문예시, HS1992…HS2022, mapping_status, note
    """
    wide = history.pivot_table(
        index=["품목명_정규화", "품목명_원문예시"],
        columns="hs_version",
        values="hs_code",
        aggfunc="first",
    ).reset_index()
    wide.columns.name = None

    # hs_version 값과 HS_COLUMNS 이름이 동일하므로 별도 rename 불필요.
    # 누락된 개정판 컬럼은 빈 문자열로 채운다.
    for col in HS_COLUMNS:
        if col not in wide.columns:
            wide[col] = ""

    # mapping_status, note는 H6(최신) 기준으로 가져온다.
    meta = (
        history[history["hs_version"] == "HS2022"][
            ["품목명_정규화", "품목명_원문예시", "mapping_status", "note"]
        ]
        .drop_duplicates(subset=["품목명_정규화"])
    )
    wide = wide.merge(meta, on=["품목명_정규화", "품목명_원문예시"], how="left")

    return wide.fillna("")


def _issue_type(row: pd.Series) -> str:
    """wide-format 행의 HS 코드 상태를 분류해 이슈 타입 문자열을 반환한다."""
    codes = [_clean_hs_code(row[col]) for col in HS_COLUMNS]
    filled = [code for code in codes if code]

    if not filled:
        return "missing_all"
    if len(filled) < len(HS_COLUMNS):
        return "partial_missing"
    if any(len(code) != 6 or not code.isdigit() for code in filled):
        return "not_six_digit"
    return "complete_6digit"


def _suggested_action(issue_type: str) -> str:
    """이슈 타입에 따른 권장 조치 문자열을 반환한다."""
    if issue_type == "missing_all":
        return "HS2022 6단위 후보를 먼저 확정한 뒤 과거 개정판으로 역매핑"
    if issue_type == "partial_missing":
        return "비어 있는 개정판 코드를 correlation table로 보완"
    if issue_type == "not_six_digit":
        return "현재 4단위/비표준 코드를 6단위 HS 코드로 세분화"
    return "완료 후보. 근거와 개정판별 변경 여부만 최종 확인"


def build_review_table(history: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """이력 테이블과 이벤트 테이블을 결합해 검토목록 DataFrame을 반환한다.

    history가 long-format(hs_revision 컬럼 존재)이면 자동으로 wide-format으로 변환한다.
    wide-format에 HS_COLUMNS가 없으면 ValueError를 발생시킨다.
    """
    # long-format 감지: hs_revision 컬럼이 있으면 pivot
    if "hs_revision" in history.columns:
        history = _pivot_long_to_wide(history)

    # wide-format 스키마 검증
    missing_cols = [col for col in HS_COLUMNS if col not in history.columns]
    if missing_cols:
        raise ValueError(
            f"history 테이블에 필요한 컬럼이 없습니다: {missing_cols}\n"
            "wide-format(HS1992~HS2022 컬럼 포함)이거나 long-format(hs_revision 컬럼 포함)이어야 합니다."
        )

    event_summary = (
        events.groupby("product_name_normalized", as_index=False)
        .agg(
            first_start=("start_date", "min"),
            last_end=("end_date", "max"),
            event_count=("event_id", "count"),
            countries=(
                "origin_country_name_kr",
                lambda values: ", ".join(sorted({v for v in values if v})),
            ),
        )
        .rename(columns={"product_name_normalized": "품목명_정규화"})
    )

    review = history.copy()
    for col in HS_COLUMNS:
        review[col] = review[col].map(_clean_hs_code)

    review["issue_type"] = review.apply(_issue_type, axis=1)
    review["suggested_action"] = review["issue_type"].map(_suggested_action)
    review = review.merge(event_summary, on="품목명_정규화", how="left")

    priority_order = {
        "missing_all": 0,
        "not_six_digit": 1,
        "partial_missing": 2,
        "complete_6digit": 3,
    }
    review["priority"] = review["issue_type"].map(priority_order)
    review = review.sort_values(["priority", "first_start", "품목명_정규화"])

    cols = [
        "issue_type",
        "suggested_action",
        "품목명_정규화",
        "품목명_원문예시",
        "first_start",
        "last_end",
        "event_count",
        "countries",
        *HS_COLUMNS,
        "note",
    ]
    return review[cols]


def build_report(review: pd.DataFrame) -> str:
    """검토목록 DataFrame을 마크다운 리포트 문자열로 변환해 반환한다."""
    counts = review["issue_type"].value_counts().reindex(
        ["missing_all", "not_six_digit", "partial_missing", "complete_6digit"],
        fill_value=0,
    )
    total = int(counts.sum())

    oldest_missing = review[review["issue_type"].eq("missing_all")].head(10)
    not_six_digit = review[review["issue_type"].eq("not_six_digit")].head(10)

    lines = [
        "# 반덤핑 HS 코드 매핑 상태",
        "",
        "## 요약",
        "",
        f"- 전체 품목 수: {total}",
        f"- 전체 미매핑: {int(counts['missing_all'])}",
        f"- 6단위 보완 필요: {int(counts['not_six_digit'])}",
        f"- 일부 개정판 누락: {int(counts['partial_missing'])}",
        f"- 6단위 완료 후보: {int(counts['complete_6digit'])}",
        "",
        "## 작업 원칙",
        "",
        "- 최종 코드는 HS 6단위 기준으로 확정한다.",
        "- 먼저 HS2022 기준 후보를 정하고, WCO/관세청 correlation table로 과거 개정판 코드를 역추적한다.",
        "- 근거가 약한 항목은 임의 확정하지 않고 `note`에 검토 필요 사유를 남긴다.",
        "- 현재 4단위 코드는 분석 투입 전 6단위로 세분화한다.",
        "",
        "## 우선 검토 대상: 전체 미매핑 상위 10개",
        "",
    ]

    if oldest_missing.empty:
        lines.append("- 없음")
    else:
        for row in oldest_missing.itertuples(index=False):
            lines.append(
                f"- {row.품목명_정규화}: {row.first_start}~{row.last_end}, "
                f"{row.event_count}건, {row.countries}"
            )

    lines.extend(["", "## 6단위 세분화 필요 상위 10개", ""])
    if not_six_digit.empty:
        lines.append("- 없음")
    else:
        for row in not_six_digit.itertuples(index=False):
            current_codes = ", ".join(
                f"{col}={getattr(row, col)}" for col in HS_COLUMNS if getattr(row, col)
            )
            lines.append(f"- {row.품목명_정규화}: {current_codes}")

    lines.extend(
        [
            "",
            "## 산출물",
            "",
            f"- 검토목록 CSV: `{REVIEW_PATH.relative_to(PROJECT_ROOT)}`",
            f"- 기준 매핑 CSV: `{HISTORY_PATH.relative_to(PROJECT_ROOT)}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    """이력 테이블과 이벤트 데이터를 읽어 검토목록 CSV와 마크다운 리포트를 생성한다."""
    history = _read_csv(HISTORY_PATH)
    events = _read_csv(EVENTS_PATH)

    review = build_review_table(history, events)
    review.to_csv(REVIEW_PATH, index=False, encoding="utf-8-sig")

    REPORTS_DIR.mkdir(exist_ok=True)
    REPORT_PATH.write_text(build_report(review), encoding="utf-8")

    print(f"wrote {REVIEW_PATH.relative_to(PROJECT_ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
