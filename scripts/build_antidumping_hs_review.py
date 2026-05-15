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


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def _clean_hs_code(value: str) -> str:
    value = value.strip()
    if value.endswith(".0"):
        value = value[:-2]
    return value.replace(".", "")


def _issue_type(row: pd.Series) -> str:
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
    if issue_type == "missing_all":
        return "HS2022 6단위 후보를 먼저 확정한 뒤 과거 개정판으로 역매핑"
    if issue_type == "partial_missing":
        return "비어 있는 개정판 코드를 correlation table로 보완"
    if issue_type == "not_six_digit":
        return "현재 4단위/비표준 코드를 6단위 HS 코드로 세분화"
    return "완료 후보. 근거와 개정판별 변경 여부만 최종 확인"


def build_review_table(history: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
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
