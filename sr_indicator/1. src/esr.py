"""ESR (Export Shift Ratio) dataset and calculation utilities.

ESR uses one row as a trade triangle:

    regulated country -> intermediary country -> importing country

For each month, the row stores two export flows from the same regulated country:
regulated -> intermediary and regulated -> importer. The ESR score can then compare
whether exports to the importer decrease while exports to the intermediary increase.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

import comtradeapicall
from src.config import get_comtrade_api_key

DEFAULT_ESR_LAGS = (0, 1, 2, 3)
DEFAULT_IMPORTER_COUNTRY = "대한민국"
ESR_PAIR_COLUMNS = [
    "사건번호",
    "품목",
    "hs_code",
    "규제국",
    "후보국",
    "분석시작월",
    "sr_min",
    "sr_best_lag",
    "sr_risk",
]
ESR_DATASET_COLUMNS = [
    "사건번호",
    "품목",
    "hs_code",
    "년월",
    "규제국",
    "중간국",
    "수입국",
    "규제국_중간국_수출량",
    "규제국_수입국_수출량",
    "규제국_중간국_수출총달러",
    "규제국_수입국_수출총달러",
    "규제국_중간국_단가",
    "규제국_수입국_단가",
    "isr_min",
    "isr_best_lag",
    "isr_risk",
]
ESR_RESULT_COLUMNS = [
    "사건번호",
    "품목",
    "hs_code",
    "규제국",
    "중간국",
    "수입국",
    "분석시작월",
    "window",
    "esr_lag0",
    "esr_lag1",
    "esr_lag2",
    "esr_lag3",
    "esr_min",
    "esr_best_lag",
    "esr_risk",
    "규제국_중간국_수출합",
    "규제국_수입국_수출합",
]


def select_isr_pairs_for_esr(
    isr_result_df: pd.DataFrame,
    max_isr_min: float = 0,
    min_isr_risk: float | None = None,
    top_n: int | None = None,
) -> pd.DataFrame:
    """Select ISR pairs to use as ESR candidate triangles.

    By default, non-positive ``sr_min`` rows are selected because those match the
    import-shift direction: regulated-country imports fall while intermediary-country
    imports rise.
    """
    missing = set(ESR_PAIR_COLUMNS) - set(isr_result_df.columns)
    if missing:
        raise ValueError(f"ISR 결과 데이터에 필수 컬럼이 없습니다: {sorted(missing)}")

    pairs = isr_result_df[ESR_PAIR_COLUMNS].copy()
    pairs = pairs[pairs["sr_min"] <= max_isr_min]

    if min_isr_risk is not None:
        pairs = pairs[pairs["sr_risk"] >= min_isr_risk]

    pairs = pairs.sort_values(["sr_risk", "sr_min"], ascending=[False, True])
    if top_n is not None:
        pairs = pairs.head(top_n)

    return pairs.reset_index(drop=True)


def make_esr_country_code_template(
    isr_pairs: pd.DataFrame,
    importer_country: str = DEFAULT_IMPORTER_COUNTRY,
) -> pd.DataFrame:
    """Create a country-code mapping template needed for Comtrade collection."""
    countries = pd.concat(
        [
            isr_pairs["규제국"],
            isr_pairs["후보국"],
            pd.Series([importer_country]),
        ],
        ignore_index=True,
    ).dropna()

    return pd.DataFrame(
        {
            "country_name_kr": sorted(countries.unique()),
            "comtrade_country_code": "",
            "reporter_code": "",
            "partner_code": "",
            "country_name_en": "",
            "note": "",
        }
    )


def build_esr_collection_plan(
    isr_pairs: pd.DataFrame,
    country_code_map: pd.DataFrame,
    importer_country: str = DEFAULT_IMPORTER_COUNTRY,
    importer_code: str = "410",
    window: int = 6,
    lags: Sequence[int] = DEFAULT_ESR_LAGS,
) -> pd.DataFrame:
    """Build a Comtrade request plan for ESR export-flow collection.

    The output has two rows per ISR pair:
    ``regulated_to_intermediary`` for 규제국 -> 중간국 and
    ``regulated_to_importer`` for 규제국 -> 수입국.
    """
    required_map_cols = {"country_name_kr", "comtrade_country_code"}
    missing_map_cols = required_map_cols - set(country_code_map.columns)
    if missing_map_cols:
        raise ValueError(f"국가코드 매핑에 필수 컬럼이 없습니다: {sorted(missing_map_cols)}")

    map_df = country_code_map.dropna(subset=["country_name_kr"]).copy()
    if "reporter_code" not in map_df.columns:
        map_df["reporter_code"] = map_df["comtrade_country_code"]
    if "partner_code" not in map_df.columns:
        map_df["partner_code"] = map_df["comtrade_country_code"]

    map_df["reporter_code"] = map_df["reporter_code"].fillna("").astype(str)
    map_df["partner_code"] = map_df["partner_code"].fillna("").astype(str)
    reporter_code_map = map_df.set_index("country_name_kr")["reporter_code"].to_dict()
    partner_code_map = map_df.set_index("country_name_kr")["partner_code"].to_dict()

    rows = []
    for idx, row in isr_pairs.reset_index(drop=True).iterrows():
        regulated_country = row["규제국"]
        intermediary_country = row["후보국"]
        regulated_code = reporter_code_map.get(regulated_country)
        intermediary_code = partner_code_map.get(intermediary_country)

        if not regulated_code or regulated_code.lower() == "nan":
            continue
        if not intermediary_code or intermediary_code.lower() == "nan":
            continue

        periods = _monthly_periods(
            start_yymm_dot=row["분석시작월"],
            months=window + max(lags),
        )
        base = {
            "pair_id": idx + 1,
            "사건번호": row["사건번호"],
            "품목": row["품목"],
            "hs_code": row["hs_code"],
            "규제국": regulated_country,
            "중간국": intermediary_country,
            "수입국": importer_country,
            "reporter_code": regulated_code,
            "periods": ",".join(periods),
            "flow_code": "X",
            "isr_min": row.get("sr_min"),
            "isr_best_lag": row.get("sr_best_lag"),
            "isr_risk": row.get("sr_risk"),
        }
        rows.append(
            {
                **base,
                "flow_type": "regulated_to_intermediary",
                "partner_code": intermediary_code,
                "partner_country": intermediary_country,
            }
        )
        rows.append(
            {
                **base,
                "flow_type": "regulated_to_importer",
                "partner_code": importer_code,
                "partner_country": importer_country,
            }
        )

    return pd.DataFrame(rows)


def build_esr_input_from_export_flows(
    isr_pairs: pd.DataFrame,
    regulated_to_intermediary_df: pd.DataFrame,
    regulated_to_importer_df: pd.DataFrame,
    importer_country: str = DEFAULT_IMPORTER_COUNTRY,
) -> pd.DataFrame:
    """Build a wide ESR input dataset from two monthly export-flow tables.

    Parameters
    ----------
    isr_pairs
        Pair table selected from ISR results. ``후보국`` is renamed to ``중간국``.
    regulated_to_intermediary_df
        Monthly exports for regulated country -> intermediary country.
    regulated_to_importer_df
        Monthly exports for regulated country -> importer country.

    Expected flow table columns
    ---------------------------
    사건번호, 품목, hs_code, 년월, 규제국, 중간국, 수출량, 수출총달러
    """
    left = _normalize_export_flow_table(
        regulated_to_intermediary_df,
        quantity_col="규제국_중간국_수출량",
        value_col="규제국_중간국_수출총달러",
        unit_price_col="규제국_중간국_단가",
    )
    right = _normalize_export_flow_table(
        regulated_to_importer_df,
        quantity_col="규제국_수입국_수출량",
        value_col="규제국_수입국_수출총달러",
        unit_price_col="규제국_수입국_단가",
    )

    key_cols = ["사건번호", "품목", "hs_code", "년월", "규제국", "중간국"]
    esr_df = left.merge(right, on=key_cols, how="outer")

    pair_meta = isr_pairs[
        ["사건번호", "품목", "hs_code", "규제국", "후보국", "sr_min", "sr_best_lag", "sr_risk"]
    ].rename(
        columns={
            "후보국": "중간국",
            "sr_min": "isr_min",
            "sr_best_lag": "isr_best_lag",
            "sr_risk": "isr_risk",
        }
    )
    esr_df = esr_df.merge(pair_meta, on=["사건번호", "품목", "hs_code", "규제국", "중간국"], how="left")
    esr_df["수입국"] = importer_country

    for col in ESR_DATASET_COLUMNS:
        if col not in esr_df.columns:
            esr_df[col] = np.nan

    return esr_df[ESR_DATASET_COLUMNS].sort_values(
        ["사건번호", "품목", "hs_code", "규제국", "중간국", "년월"]
    ).reset_index(drop=True)


def calculate_esr_with_lags(
    esr_input_df: pd.DataFrame,
    window: int = 6,
    lags: Sequence[int] = DEFAULT_ESR_LAGS,
    min_total_export: float = 0,
) -> pd.DataFrame:
    """Calculate ESR from the wide triangle-flow dataset.

    ESR compares ``규제국_수입국_수출량`` with lagged ``규제국_중간국_수출량``.
    Negative correlation is treated as higher export-shift risk.
    """
    required = {
        "사건번호",
        "품목",
        "hs_code",
        "년월",
        "규제국",
        "중간국",
        "수입국",
        "규제국_중간국_수출량",
        "규제국_수입국_수출량",
    }
    missing = required - set(esr_input_df.columns)
    if missing:
        raise ValueError(f"ESR 입력 데이터에 필수 컬럼이 없습니다: {sorted(missing)}")
    if window < 2:
        raise ValueError("window must be at least 2 for Spearman correlation.")
    if not lags:
        raise ValueError("lags must contain at least one lag value.")

    df = esr_input_df.copy()
    df = df[df["년월"].astype(str).str.match(r"^\d{4}\.\d{2}$")].copy()
    df["년월_dt"] = pd.to_datetime(df["년월"].astype(str), format="%Y.%m")
    df["규제국_중간국_수출량"] = pd.to_numeric(
        df["규제국_중간국_수출량"], errors="coerce"
    ).fillna(0)
    df["규제국_수입국_수출량"] = pd.to_numeric(
        df["규제국_수입국_수출량"], errors="coerce"
    ).fillna(0)

    results = []
    sorted_lags = sorted(set(int(lag) for lag in lags))
    group_cols = ["사건번호", "품목", "hs_code", "규제국", "중간국", "수입국"]

    for group_key, group in df.groupby(group_cols):
        case_id, product_name, hs_code, regulated_country, intermediary_country, importer_country = group_key
        group = group.sort_values("년월_dt").copy()
        start_month = group["년월_dt"].min()
        full_months = pd.date_range(start=start_month, periods=window + max(sorted_lags), freq="MS")

        monthly = (
            group.set_index("년월_dt")[
                ["규제국_중간국_수출량", "규제국_수입국_수출량"]
            ]
            .reindex(full_months)
            .fillna(0)
        )

        importer_series = monthly["규제국_수입국_수출량"].iloc[:window].reset_index(drop=True)
        intermediary_full = monthly["규제국_중간국_수출량"]

        if importer_series.nunique() <= 1 or intermediary_full.sum() <= min_total_export:
            continue

        esr_by_lag: dict[str, float] = {}
        for lag in sorted_lags:
            intermediary_series = intermediary_full.iloc[lag : lag + window].reset_index(drop=True)
            if len(intermediary_series) < window or intermediary_series.nunique() <= 1:
                esr_by_lag[f"esr_lag{lag}"] = np.nan
                continue

            esr_value, _ = spearmanr(importer_series, intermediary_series)
            esr_by_lag[f"esr_lag{lag}"] = esr_value

        valid_esrs = {
            lag: esr_by_lag.get(f"esr_lag{lag}")
            for lag in sorted_lags
            if pd.notna(esr_by_lag.get(f"esr_lag{lag}"))
        }
        if valid_esrs:
            esr_best_lag = min(valid_esrs, key=valid_esrs.get)
            esr_min = valid_esrs[esr_best_lag]
            esr_risk = max(0, -esr_min)
        else:
            esr_best_lag = np.nan
            esr_min = np.nan
            esr_risk = np.nan

        results.append(
            {
                "사건번호": case_id,
                "품목": product_name,
                "hs_code": hs_code,
                "규제국": regulated_country,
                "중간국": intermediary_country,
                "수입국": importer_country,
                "분석시작월": start_month.strftime("%Y.%m"),
                "window": window,
                **esr_by_lag,
                "esr_min": esr_min,
                "esr_best_lag": esr_best_lag,
                "esr_risk": esr_risk,
                "규제국_중간국_수출합": intermediary_full.iloc[: window + max(sorted_lags)].sum(),
                "규제국_수입국_수출합": importer_series.sum(),
            }
        )

    return pd.DataFrame(results)


def collect_esr_export_flow_dataset(
    collection_plan: pd.DataFrame,
    max_requests: int | None = None,
    max_records: int = 250_000,
) -> pd.DataFrame:
    """Collect Comtrade exports and build the wide ESR input dataset.

    Parameters
    ----------
    collection_plan
        Output from ``build_esr_collection_plan``.
    max_requests
        Optional cap for test runs.
    max_records
        Comtrade ``maxRecords`` per request.

    Returns
    -------
    pd.DataFrame
        ESR wide input dataset with one row per triangle-month.
    """
    required = {
        "pair_id",
        "사건번호",
        "품목",
        "hs_code",
        "규제국",
        "중간국",
        "수입국",
        "reporter_code",
        "periods",
        "flow_code",
        "isr_min",
        "isr_best_lag",
        "isr_risk",
        "flow_type",
        "partner_code",
    }
    missing = required - set(collection_plan.columns)
    if missing:
        raise ValueError(f"ESR 수집계획에 필수 컬럼이 없습니다: {sorted(missing)}")

    api_key = get_comtrade_api_key()
    rows = []
    plan = collection_plan.copy()
    if max_requests is not None:
        plan = plan.head(max_requests)

    for request_idx, request in plan.iterrows():
        print(
            "Collecting ESR "
            f"{request_idx + 1}/{len(plan)} "
            f"pair={request['pair_id']} "
            f"{request['규제국']}->{request.get('partner_country', request['partner_code'])} "
            f"hs={request['hs_code']}"
        )

        response_df = comtradeapicall.getFinalData(
            api_key,
            typeCode="C",
            freqCode="M",
            clCode="HS",
            period=str(request["periods"]),
            reporterCode=str(request["reporter_code"]),
            cmdCode=str(request["hs_code"]),
            flowCode=str(request["flow_code"]),
            partnerCode=str(request["partner_code"]),
            partner2Code=None,
            customsCode=None,
            motCode=None,
            maxRecords=max_records,
            format_output="JSON",
            aggregateBy=None,
            breakdownMode="plus",
            countOnly=None,
            includeDesc=True,
        )

        rows.extend(_comtrade_response_to_esr_rows(request, response_df))

    if not rows:
        return pd.DataFrame(columns=ESR_DATASET_COLUMNS)

    long_df = pd.DataFrame(rows)
    return _wide_esr_dataset_from_long_rows(long_df)


def _normalize_export_flow_table(
    export_df: pd.DataFrame,
    quantity_col: str,
    value_col: str,
    unit_price_col: str,
) -> pd.DataFrame:
    required = {"사건번호", "품목", "hs_code", "년월", "규제국", "중간국", "수출량", "수출총달러"}
    missing = required - set(export_df.columns)
    if missing:
        raise ValueError(f"수출 흐름 데이터에 필수 컬럼이 없습니다: {sorted(missing)}")

    df = export_df.copy()
    df[quantity_col] = pd.to_numeric(df["수출량"], errors="coerce").fillna(0)
    df[value_col] = pd.to_numeric(df["수출총달러"], errors="coerce").fillna(0)
    df[unit_price_col] = np.where(df[quantity_col] > 0, df[value_col] / df[quantity_col], np.nan)

    return df[
        [
            "사건번호",
            "품목",
            "hs_code",
            "년월",
            "규제국",
            "중간국",
            quantity_col,
            value_col,
            unit_price_col,
        ]
    ]


def _comtrade_response_to_esr_rows(request: pd.Series, response_df: pd.DataFrame | None) -> list[dict]:
    periods = str(request["periods"]).split(",")
    monthly = {period: {"수출량": 0.0, "수출총달러": 0.0} for period in periods}

    if response_df is not None and isinstance(response_df, pd.DataFrame) and not response_df.empty:
        df = response_df.copy()
        period_col = "period" if "period" in df.columns else None
        if period_col is None and {"refYear", "refMonth"}.issubset(df.columns):
            df["period"] = (
                df["refYear"].astype(int).astype(str)
                + df["refMonth"].astype(int).astype(str).str.zfill(2)
            )
            period_col = "period"

        if period_col is not None:
            value_col = "primaryValue" if "primaryValue" in df.columns else None
            quantity_col = _choose_comtrade_quantity_col(df)
            grouped = df.groupby(period_col, dropna=False).agg(
                수출총달러=(value_col, "sum") if value_col else (df.columns[0], "size"),
                수출량=(quantity_col, "sum") if quantity_col else (df.columns[0], "size"),
            )
            for period, values in grouped.iterrows():
                period_key = str(period)
                if period_key.endswith(".0"):
                    period_key = period_key[:-2]
                if period_key in monthly:
                    monthly[period_key]["수출량"] = float(values["수출량"])
                    monthly[period_key]["수출총달러"] = float(values["수출총달러"])

    rows = []
    for period, values in monthly.items():
        rows.append(
            {
                "pair_id": request["pair_id"],
                "사건번호": request["사건번호"],
                "품목": request["품목"],
                "hs_code": request["hs_code"],
                "년월": f"{period[:4]}.{period[4:6]}",
                "규제국": request["규제국"],
                "중간국": request["중간국"],
                "수입국": request["수입국"],
                "flow_type": request["flow_type"],
                "수출량": values["수출량"],
                "수출총달러": values["수출총달러"],
                "isr_min": request["isr_min"],
                "isr_best_lag": request["isr_best_lag"],
                "isr_risk": request["isr_risk"],
            }
        )
    return rows


def _choose_comtrade_quantity_col(df: pd.DataFrame) -> str | None:
    for col in ["netWgt", "qty", "altQty", "grossWgt"]:
        if col in df.columns:
            return col
    return None


def _wide_esr_dataset_from_long_rows(long_df: pd.DataFrame) -> pd.DataFrame:
    key_cols = ["사건번호", "품목", "hs_code", "년월", "규제국", "중간국", "수입국"]
    meta_cols = ["isr_min", "isr_best_lag", "isr_risk"]

    value_frames = []
    for flow_type, prefix in [
        ("regulated_to_intermediary", "규제국_중간국"),
        ("regulated_to_importer", "규제국_수입국"),
    ]:
        flow_df = long_df[long_df["flow_type"] == flow_type].copy()
        flow_df = flow_df.rename(
            columns={
                "수출량": f"{prefix}_수출량",
                "수출총달러": f"{prefix}_수출총달러",
            }
        )
        value_frames.append(
            flow_df[key_cols + [f"{prefix}_수출량", f"{prefix}_수출총달러"]]
        )

    esr_df = value_frames[0].merge(value_frames[1], on=key_cols, how="outer")
    meta = long_df[key_cols + meta_cols].drop_duplicates(key_cols)
    esr_df = esr_df.merge(meta, on=key_cols, how="left")

    for prefix in ["규제국_중간국", "규제국_수입국"]:
        qty_col = f"{prefix}_수출량"
        value_col = f"{prefix}_수출총달러"
        unit_col = f"{prefix}_단가"
        esr_df[qty_col] = pd.to_numeric(esr_df[qty_col], errors="coerce").fillna(0)
        esr_df[value_col] = pd.to_numeric(esr_df[value_col], errors="coerce").fillna(0)
        esr_df[unit_col] = np.where(esr_df[qty_col] > 0, esr_df[value_col] / esr_df[qty_col], np.nan)

    for col in ESR_DATASET_COLUMNS:
        if col not in esr_df.columns:
            esr_df[col] = np.nan

    return esr_df[ESR_DATASET_COLUMNS].sort_values(
        ["사건번호", "품목", "hs_code", "규제국", "중간국", "년월"]
    ).reset_index(drop=True)


def _monthly_periods(start_yymm_dot: str, months: int) -> list[str]:
    start = pd.to_datetime(str(start_yymm_dot), format="%Y.%m")
    return [period.strftime("%Y%m") for period in pd.date_range(start=start, periods=months, freq="MS")]


def save_esr_dataset(esr_df: pd.DataFrame, path: str) -> None:
    """Save an ESR dataset as UTF-8 CSV."""
    esr_df.to_csv(path, index=False, encoding="utf-8-sig")
