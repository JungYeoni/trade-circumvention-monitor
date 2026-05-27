"""ISR (Import Shift Ratio) calculation utilities.

ISR compares import quantity patterns between a regulated country and a
candidate non-regulated country after a trade remedy event. It uses Spearman
rank correlation across several lag windows and treats stronger negative
correlation as higher import-shift risk.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

DEFAULT_ISR_LAGS = (0, 1, 2, 3)
ISR_REQUIRED_COLUMNS = {
    "사건번호",
    "국가",
    "품목",
    "hs_code",
    "년월",
    "수입량",
    "규제국여부",
}


def validate_isr_input(df: pd.DataFrame) -> None:
    """Validate the minimum input columns needed for ISR calculation."""
    missing = ISR_REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"ISR 입력 데이터에 필수 컬럼이 없습니다: {sorted(missing)}")


def calculate_isr_with_lags(
    import_df: pd.DataFrame,
    window: int = 6,
    lags: Sequence[int] = DEFAULT_ISR_LAGS,
    min_total_import: float = 0,
) -> pd.DataFrame:
    """Calculate ISR for regulated-country and candidate-country import pairs.

    Parameters
    ----------
    import_df
        Input import table. Expected columns include 사건번호, 국가, 품목, hs_code, 년월,
        수입량, and 규제국여부.
    window
        Number of months used for the regulated-country reference series.
    lags
        Candidate-country lag windows to compare. Default is 0 to 3 months.
    min_total_import
        Candidate countries with total import quantity at or below this value are skipped.

    Returns
    -------
    pd.DataFrame
        ISR result table. Column names keep the existing sr_* convention for
        compatibility with the current dataset.
    """
    validate_isr_input(import_df)
    if window < 2:
        raise ValueError("window must be at least 2 for Spearman correlation.")
    if not lags:
        raise ValueError("lags must contain at least one lag value.")
    if min(lags) < 0:
        raise ValueError("lags must be non-negative.")

    df = import_df.copy()
    df = df[df["년월"].astype(str).str.match(r"^\d{4}\.\d{2}$")].copy()
    df["년월_dt"] = pd.to_datetime(df["년월"].astype(str), format="%Y.%m")
    df["수입량"] = pd.to_numeric(df["수입량"], errors="coerce").fillna(0)

    results = []
    group_cols = ["사건번호", "품목", "hs_code"]
    sorted_lags = sorted(set(int(lag) for lag in lags))

    for (case_id, product_name, hs_code), group in df.groupby(group_cols):
        group = group.copy()
        start_month = group["년월_dt"].min()
        full_months = pd.date_range(
            start=start_month,
            periods=window + max(sorted_lags),
            freq="MS",
        )

        pivot = (
            group.pivot_table(
                index="년월_dt",
                columns="국가",
                values="수입량",
                aggfunc="sum",
            )
            .reindex(full_months)
            .fillna(0)
        )

        regulated_countries = (
            group.loc[group["규제국여부"] == True, "국가"].dropna().unique().tolist()
        )
        candidate_countries = (
            group.loc[group["규제국여부"] == False, "국가"].dropna().unique().tolist()
        )

        for regulated_country in regulated_countries:
            if regulated_country not in pivot.columns:
                continue

            regulated_series = pivot[regulated_country].iloc[:window].reset_index(drop=True)
            if regulated_series.nunique() <= 1:
                continue

            for candidate_country in candidate_countries:
                if candidate_country not in pivot.columns:
                    continue

                candidate_full = pivot[candidate_country]
                if candidate_full.sum() <= min_total_import:
                    continue

                sr_by_lag: dict[str, float] = {}
                for lag in sorted_lags:
                    candidate_series = candidate_full.iloc[lag : lag + window].reset_index(
                        drop=True
                    )

                    if len(candidate_series) < window or candidate_series.nunique() <= 1:
                        sr_by_lag[f"sr_lag{lag}"] = np.nan
                        continue

                    sr_value, _ = spearmanr(regulated_series, candidate_series)
                    sr_by_lag[f"sr_lag{lag}"] = sr_value

                valid_srs = {
                    lag: sr_by_lag.get(f"sr_lag{lag}")
                    for lag in sorted_lags
                    if pd.notna(sr_by_lag.get(f"sr_lag{lag}"))
                }

                if valid_srs:
                    sr_best_lag = min(valid_srs, key=valid_srs.get)
                    sr_min = valid_srs[sr_best_lag]
                    sr_risk = max(0, -sr_min)
                else:
                    sr_best_lag = np.nan
                    sr_min = np.nan
                    sr_risk = np.nan

                results.append(
                    {
                        "사건번호": case_id,
                        "품목": product_name,
                        "hs_code": hs_code,
                        "규제국": regulated_country,
                        "후보국": candidate_country,
                        "분석시작월": start_month.strftime("%Y.%m"),
                        "window": window,
                        **sr_by_lag,
                        "sr_min": sr_min,
                        "sr_best_lag": sr_best_lag,
                        "sr_risk": sr_risk,
                        "규제국_6개월_수입합": regulated_series.sum(),
                        "후보국_전체기간_수입합": candidate_full.sum(),
                    }
                )

    return pd.DataFrame(results)


def load_isr_input(path: str) -> pd.DataFrame:
    """Load an ISR input CSV."""
    return pd.read_csv(path)


def save_isr_result(result_df: pd.DataFrame, path: str) -> None:
    """Save ISR results as UTF-8 CSV."""
    result_df.to_csv(path, index=False, encoding="utf-8-sig")
