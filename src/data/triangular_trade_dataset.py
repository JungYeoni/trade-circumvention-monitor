"""Build and collect event-level triangular trade panel data.

One panel row represents this triangle for one month:

    regulated country -> intermediary country -> Korea

Data source rule:
- Korea-involved flows use Korea Customs data.
- Foreign-to-foreign flows use UN Comtrade data.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from pathlib import Path

import comtradeapicall
import pandas as pd
import requests

from src.config import get_comtrade_api_key, get_customs_api_key

KOREA_COUNTRY_NAME = "대한민국"
KOREA_CUSTOMS_CODE = "KR"
KOREA_COMTRADE_CODE = "410"

FLOW_REGULATED_TO_INTERMEDIARY = "regulated_to_intermediary"
FLOW_INTERMEDIARY_TO_KOREA = "intermediary_to_korea"
FLOW_REGULATED_TO_KOREA = "regulated_to_korea"

SOURCE_COMTRADE = "UN_COMTRADE"
SOURCE_CUSTOMS = "CUSTOMS"

FLOW_TO_VALUE_COLUMNS = {
    FLOW_REGULATED_TO_INTERMEDIARY: (
        "규제국_중간국_수출량",
        "규제국_중간국_수출총달러",
        "규제국_중간국_source",
    ),
    FLOW_INTERMEDIARY_TO_KOREA: (
        "중간국_한국_수출량",
        "중간국_한국_수출총달러",
        "중간국_한국_source",
    ),
    FLOW_REGULATED_TO_KOREA: (
        "규제국_한국_수출량",
        "규제국_한국_수출총달러",
        "규제국_한국_source",
    ),
}

PLAN_COLUMNS = [
    "request_id",
    "event_id",
    "flow_type",
    "source",
    "regulated_country",
    "intermediary_country",
    "importer_country",
    "reporter_country",
    "partner_country",
    "reporter_code",
    "partner_code",
    "customs_country_code",
    "hs_code",
    "periods",
    "start_yymm",
    "end_yymm",
    "product_name",
    "duty_text_raw",
    "duty_type",
    "duty_rate_min",
    "duty_rate_max",
    "start_date",
    "end_date",
]

LONG_COLUMNS = [
    "request_id",
    "event_id",
    "flow_type",
    "source",
    "regulated_country",
    "intermediary_country",
    "importer_country",
    "reporter_country",
    "partner_country",
    "hs_code",
    "year_month",
    "quantity",
    "value_usd",
]

STATUS_COLUMNS = ["request_id", "status", "rows", "error", "started_at", "finished_at"]


def make_month_periods(
    start_date: str | pd.Timestamp, end_date: str | pd.Timestamp
) -> list[str]:
    """Return YYYYMM month periods from start month to end month inclusive."""
    start = pd.Period(pd.to_datetime(start_date), freq="M")
    end = pd.Period(pd.to_datetime(end_date), freq="M")
    if end < start:
        raise ValueError("end_date must be greater than or equal to start_date.")
    return [period.strftime("%Y%m") for period in pd.period_range(start, end, freq="M")]


def event_collection_window(
    start_date: str | pd.Timestamp,
    end_date: str | pd.Timestamp,
    today: str | pd.Timestamp | date | None = None,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Return regulation window: start - 1 year through min(end + 1 year, today)."""
    today_ts = (
        pd.Timestamp.today().normalize()
        if today is None
        else pd.to_datetime(today).normalize()
    )
    collection_start = pd.to_datetime(start_date) - pd.DateOffset(years=1)
    collection_end = min(pd.to_datetime(end_date) + pd.DateOffset(years=1), today_ts)
    return collection_start.normalize(), collection_end.normalize()


def make_triangular_trade_collection_plan(
    regulation_events: pd.DataFrame,
    intermediary_candidates: pd.DataFrame,
    country_code_map: pd.DataFrame,
    today: str | pd.Timestamp | date | None = None,
    importer_country: str = KOREA_COUNTRY_NAME,
    importer_comtrade_code: str = KOREA_COMTRADE_CODE,
) -> pd.DataFrame:
    """Create one request-plan row per event, intermediary, and flow.

    ``intermediary_candidates`` must contain ``event_id`` and ``intermediary_country``.
    ``country_code_map`` must contain Korean country names and both Comtrade and
    Customs codes.
    """
    _require_columns(
        regulation_events,
        {
            "event_id",
            "origin_country_name_kr",
            "product_name_kr",
            "hs_code",
            "start_date",
            "end_date",
        },
        "regulation_events",
    )
    _require_columns(
        intermediary_candidates,
        {"event_id", "intermediary_country"},
        "intermediary_candidates",
    )
    _require_columns(
        country_code_map,
        {
            "country_name_kr",
            "comtrade_reporter_code",
            "comtrade_partner_code",
            "customs_country_code",
        },
        "country_code_map",
    )

    code_map = country_code_map.fillna("").astype(str).set_index("country_name_kr")
    event_cols = [
        "event_id",
        "origin_country_name_kr",
        "product_name_kr",
        "hs_code",
        "start_date",
        "end_date",
    ]
    optional_cols = ["duty_text_raw", "duty_type", "duty_rate_min", "duty_rate_max"]
    event_cols.extend(
        [col for col in optional_cols if col in regulation_events.columns]
    )

    events = regulation_events[event_cols].copy()
    pairs = events.merge(intermediary_candidates, on="event_id", how="inner")
    rows = []

    for _, row in pairs.iterrows():
        regulated_country = str(row["origin_country_name_kr"])
        intermediary_country = str(row["intermediary_country"])
        if not row.get("hs_code") or pd.isna(row.get("hs_code")):
            continue
        if (
            regulated_country == intermediary_country
            or intermediary_country == importer_country
        ):
            continue

        regulated_codes = _lookup_country_codes(code_map, regulated_country)
        intermediary_codes = _lookup_country_codes(code_map, intermediary_country)
        if regulated_codes is None or intermediary_codes is None:
            continue

        collection_start, collection_end = event_collection_window(
            row["start_date"], row["end_date"], today=today
        )
        periods = make_month_periods(collection_start, collection_end)
        if not periods:
            continue

        base = {
            "event_id": row["event_id"],
            "regulated_country": regulated_country,
            "intermediary_country": intermediary_country,
            "importer_country": importer_country,
            "hs_code": str(row["hs_code"]),
            "periods": ",".join(periods),
            "start_yymm": periods[0],
            "end_yymm": periods[-1],
            "product_name": row["product_name_kr"],
            "duty_text_raw": row.get("duty_text_raw", pd.NA),
            "duty_type": row.get("duty_type", pd.NA),
            "duty_rate_min": row.get("duty_rate_min", pd.NA),
            "duty_rate_max": row.get("duty_rate_max", pd.NA),
            "start_date": row["start_date"],
            "end_date": row["end_date"],
        }
        rows.extend(
            [
                {
                    **base,
                    "flow_type": FLOW_REGULATED_TO_INTERMEDIARY,
                    "source": SOURCE_COMTRADE,
                    "reporter_country": regulated_country,
                    "partner_country": intermediary_country,
                    "reporter_code": regulated_codes["comtrade_reporter_code"],
                    "partner_code": intermediary_codes["comtrade_partner_code"],
                    "customs_country_code": "",
                },
                {
                    **base,
                    "flow_type": FLOW_INTERMEDIARY_TO_KOREA,
                    "source": SOURCE_CUSTOMS,
                    "reporter_country": intermediary_country,
                    "partner_country": importer_country,
                    "reporter_code": "",
                    "partner_code": importer_comtrade_code,
                    "customs_country_code": intermediary_codes["customs_country_code"],
                },
                {
                    **base,
                    "flow_type": FLOW_REGULATED_TO_KOREA,
                    "source": SOURCE_CUSTOMS,
                    "reporter_country": regulated_country,
                    "partner_country": importer_country,
                    "reporter_code": "",
                    "partner_code": importer_comtrade_code,
                    "customs_country_code": regulated_codes["customs_country_code"],
                },
            ]
        )

    plan = pd.DataFrame(rows)
    if plan.empty:
        return pd.DataFrame(columns=PLAN_COLUMNS)
    plan.insert(0, "request_id", [f"REQ-{idx + 1:08d}" for idx in range(len(plan))])
    return plan[PLAN_COLUMNS]


def collect_triangular_trade_with_resume(
    plan_path: str | Path,
    status_path: str | Path,
    long_raw_path: str | Path,
    panel_partial_path: str | Path | None = None,
    checkpoint_every: int = 20,
    stop_on_quota: bool = True,
) -> None:
    """Collect a triangular trade request plan with checkpoint/resume support."""
    plan_path = Path(plan_path)
    status_path = Path(status_path)
    long_raw_path = Path(long_raw_path)
    panel_partial_path = (
        Path(panel_partial_path) if panel_partial_path is not None else None
    )

    plan = pd.read_csv(plan_path, dtype=str).fillna("")
    status = _read_csv_or_empty(status_path, STATUS_COLUMNS)
    long_df = _read_csv_or_empty(long_raw_path, LONG_COLUMNS)
    ok_request_ids = set(status.loc[status["status"].eq("ok"), "request_id"])

    status_records = status.to_dict("records")
    long_records = long_df.to_dict("records")
    comtrade_api_key = get_comtrade_api_key()
    customs_api_key = get_customs_api_key()

    processed_since_checkpoint = 0
    for _, request in plan.iterrows():
        request_id = request["request_id"]
        if request_id in ok_request_ids:
            continue

        started_at = pd.Timestamp.now().isoformat(timespec="seconds")
        try:
            rows = collect_one_triangular_request(
                request, comtrade_api_key, customs_api_key
            )
            long_records.extend(rows)
            status_records.append(
                {
                    "request_id": request_id,
                    "status": "ok",
                    "rows": str(len(rows)),
                    "error": "",
                    "started_at": started_at,
                    "finished_at": pd.Timestamp.now().isoformat(timespec="seconds"),
                }
            )
            ok_request_ids.add(request_id)
            processed_since_checkpoint += 1
        except ComtradeQuotaError as exc:
            status_records.append(
                {
                    "request_id": request_id,
                    "status": "quota_stopped",
                    "rows": "0",
                    "error": str(exc),
                    "started_at": started_at,
                    "finished_at": pd.Timestamp.now().isoformat(timespec="seconds"),
                }
            )
            _write_triangular_checkpoint(
                status_path,
                long_raw_path,
                panel_partial_path,
                status_records,
                long_records,
                plan,
            )
            if stop_on_quota:
                return
        except Exception as exc:  # noqa: BLE001 - keep resumable batch collection.
            status_records.append(
                {
                    "request_id": request_id,
                    "status": "error",
                    "rows": "0",
                    "error": repr(exc)[:500],
                    "started_at": started_at,
                    "finished_at": pd.Timestamp.now().isoformat(timespec="seconds"),
                }
            )
            processed_since_checkpoint += 1

        if processed_since_checkpoint >= checkpoint_every:
            _write_triangular_checkpoint(
                status_path,
                long_raw_path,
                panel_partial_path,
                status_records,
                long_records,
                plan,
            )
            processed_since_checkpoint = 0

    _write_triangular_checkpoint(
        status_path,
        long_raw_path,
        panel_partial_path,
        status_records,
        long_records,
        plan,
    )


def collect_one_triangular_request(
    request: pd.Series,
    comtrade_api_key: str | None = None,
    customs_api_key: str | None = None,
) -> list[dict]:
    """Collect one plan row and return normalized monthly long rows."""
    if request["source"] == SOURCE_COMTRADE:
        response_df = comtradeapicall.getFinalData(
            comtrade_api_key or get_comtrade_api_key(),
            typeCode="C",
            freqCode="M",
            clCode="HS",
            period=request["periods"],
            reporterCode=str(request["reporter_code"]),
            cmdCode=str(request["hs_code"]),
            flowCode="X",
            partnerCode=str(request["partner_code"]),
            partner2Code=None,
            customsCode=None,
            motCode=None,
            maxRecords=250_000,
            format_output="JSON",
            aggregateBy=None,
            breakdownMode="plus",
            countOnly=None,
            includeDesc=True,
        )
        if response_df is None:
            raise ComtradeQuotaError(
                "UN Comtrade returned an empty response. This may indicate quota exhaustion."
            )
        return normalize_comtrade_response(request, response_df)

    if request["source"] == SOURCE_CUSTOMS:
        response_df = collect_customs_request(request, customs_api_key=customs_api_key)
        return normalize_customs_response(request, response_df)

    raise ValueError(f"Unknown source: {request['source']}")


def collect_customs_request(
    request: pd.Series, customs_api_key: str | None = None
) -> pd.DataFrame:
    """Collect one Korea Customs request from a plan row."""
    api_key = customs_api_key or get_customs_api_key()
    params = {
        "serviceKey": api_key,
        "strtYymm": request["start_yymm"],
        "endYymm": request["end_yymm"],
        "hsSgn": str(request["hs_code"]),
        "cntyCd": str(request["customs_country_code"]),
        "type": "json",
    }
    response = requests.get(
        "https://apis.data.go.kr/1220000/nitemtrade/getNitemtradeList",
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    items = _extract_customs_items(data)
    return pd.DataFrame(items)


def normalize_comtrade_response(
    request: pd.Series, response_df: pd.DataFrame
) -> list[dict]:
    """Normalize UN Comtrade response to monthly long rows."""
    periods = request["periods"].split(",")
    if response_df is None or response_df.empty:
        return [_empty_long_row(request, period) for period in periods]

    df = response_df.copy()
    year_col = _first_existing_column(df, ["refYear", "period"])
    month_col = _first_existing_column(df, ["refMonth"])
    quantity_col = _first_existing_column(
        df, ["qty", "netWgt", "grossWgt", "primaryQuantity"]
    )
    value_col = _first_existing_column(df, ["primaryValue", "fobvalue", "cifvalue"])

    df["year_month"] = _coerce_year_month(df, year_col, month_col)
    if quantity_col:
        df[quantity_col] = pd.to_numeric(df[quantity_col], errors="coerce").fillna(0)
    if value_col:
        df[value_col] = pd.to_numeric(df[value_col], errors="coerce").fillna(0)
    grouped = (
        df.groupby("year_month", dropna=False)
        .agg(
            quantity=(quantity_col, "sum") if quantity_col else ("year_month", "size"),
            value_usd=(value_col, "sum") if value_col else ("year_month", "size"),
        )
        .reset_index()
    )
    rows_by_month = {
        str(row["year_month"]): _base_long_row(
            request,
            str(row["year_month"]),
            quantity=row["quantity"] if quantity_col else pd.NA,
            value_usd=row["value_usd"] if value_col else pd.NA,
        )
        for _, row in grouped.iterrows()
    }
    return [
        rows_by_month.get(period, _empty_long_row(request, period))
        for period in periods
    ]


def normalize_customs_response(
    request: pd.Series, response_df: pd.DataFrame
) -> list[dict]:
    """Normalize Korea Customs response to monthly long rows."""
    periods = request["periods"].split(",")
    if response_df is None or response_df.empty:
        return [_empty_long_row(request, period) for period in periods]

    df = response_df.copy()
    period_col = _first_existing_column(
        df, ["year", "statKor", "baseYm", "yymm", "trdeYymm"]
    )
    quantity_col = _first_existing_column(df, ["impWgt", "expWgt", "qty", "imxprQy"])
    value_col = _first_existing_column(
        df, ["impDlr", "expDlr", "usdAmt", "imxprUsdAmt"]
    )
    if period_col is None:
        df["year_month"] = pd.NA
    else:
        df["year_month"] = df[period_col].map(_normalize_yymm_value)
    if quantity_col:
        df[quantity_col] = pd.to_numeric(df[quantity_col], errors="coerce").fillna(0)
    if value_col:
        df[value_col] = pd.to_numeric(df[value_col], errors="coerce").fillna(0)

    grouped = (
        df.dropna(subset=["year_month"])
        .groupby("year_month", dropna=False)
        .agg(
            quantity=(quantity_col, "sum") if quantity_col else ("year_month", "size"),
            value_usd=(value_col, "sum") if value_col else ("year_month", "size"),
        )
        .reset_index()
    )
    rows_by_month = {
        str(row["year_month"]): _base_long_row(
            request,
            str(row["year_month"]),
            quantity=row["quantity"] if quantity_col else pd.NA,
            value_usd=row["value_usd"] if value_col else pd.NA,
        )
        for _, row in grouped.iterrows()
    }
    return [
        rows_by_month.get(period, _empty_long_row(request, period))
        for period in periods
    ]


def build_triangular_trade_panel(
    long_df: pd.DataFrame, plan_df: pd.DataFrame
) -> pd.DataFrame:
    """Build the wide triangular panel from normalized long flow rows."""
    if long_df.empty:
        return pd.DataFrame()

    meta_cols = [
        "event_id",
        "regulated_country",
        "intermediary_country",
        "importer_country",
        "hs_code",
        "product_name",
        "duty_text_raw",
        "duty_type",
        "duty_rate_min",
        "duty_rate_max",
        "start_date",
        "end_date",
    ]
    meta = plan_df[meta_cols].drop_duplicates()
    key_cols = [
        "event_id",
        "regulated_country",
        "intermediary_country",
        "importer_country",
        "hs_code",
        "year_month",
    ]
    base = long_df[key_cols].drop_duplicates()

    panel = base.merge(
        meta,
        on=[
            "event_id",
            "regulated_country",
            "intermediary_country",
            "importer_country",
            "hs_code",
        ],
        how="left",
    )
    for flow_type, (
        quantity_col,
        value_col,
        source_col,
    ) in FLOW_TO_VALUE_COLUMNS.items():
        flow = long_df[long_df["flow_type"].eq(flow_type)][
            key_cols + ["quantity", "value_usd", "source"]
        ].rename(
            columns={
                "quantity": quantity_col,
                "value_usd": value_col,
                "source": source_col,
            }
        )
        panel = panel.merge(flow, on=key_cols, how="left")

    return panel.sort_values(
        [
            "event_id",
            "hs_code",
            "regulated_country",
            "intermediary_country",
            "year_month",
        ]
    ).reset_index(drop=True)


class ComtradeQuotaError(RuntimeError):
    """Raised when Comtrade likely stops because of request quota."""


def _write_triangular_checkpoint(
    status_path: Path,
    long_raw_path: Path,
    panel_partial_path: Path | None,
    status_records: list[dict],
    long_records: list[dict],
    plan_df: pd.DataFrame,
) -> None:
    status_path.parent.mkdir(parents=True, exist_ok=True)
    long_raw_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(status_records, columns=STATUS_COLUMNS).to_csv(
        status_path, index=False, encoding="utf-8-sig"
    )
    long_df = pd.DataFrame(long_records, columns=LONG_COLUMNS)
    long_df.to_csv(long_raw_path, index=False, encoding="utf-8-sig")
    if panel_partial_path is not None:
        panel_partial_path.parent.mkdir(parents=True, exist_ok=True)
        build_triangular_trade_panel(long_df, plan_df).to_csv(
            panel_partial_path, index=False, encoding="utf-8-sig"
        )


def _read_csv_or_empty(path: Path, columns: Iterable[str]) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path, dtype=str).fillna("")
    return pd.DataFrame(columns=list(columns))


def _lookup_country_codes(
    code_map: pd.DataFrame, country_name: str
) -> dict[str, str] | None:
    if country_name not in code_map.index:
        return None
    row = code_map.loc[country_name]
    return {
        "comtrade_reporter_code": str(row["comtrade_reporter_code"]),
        "comtrade_partner_code": str(row["comtrade_partner_code"]),
        "customs_country_code": str(row["customs_country_code"]),
    }


def _require_columns(df: pd.DataFrame, required: set[str], name: str) -> None:
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{name} is missing required columns: {sorted(missing)}")


def _extract_customs_items(data: dict) -> list[dict]:
    body = data.get("response", {}).get("body", {})
    items = body.get("items", {})
    item = items.get("item", []) if isinstance(items, dict) else items
    if isinstance(item, dict):
        return [item]
    if isinstance(item, list):
        return item
    return []


def _first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for column in candidates:
        if column in df.columns:
            return column
    return None


def _coerce_year_month(
    df: pd.DataFrame, year_col: str | None, month_col: str | None
) -> pd.Series:
    if year_col is None:
        return pd.Series(pd.NA, index=df.index)
    if month_col is None:
        return df[year_col].map(_normalize_yymm_value)
    return df[year_col].astype(str).str.zfill(4) + df[month_col].astype(str).str.zfill(
        2
    )


def _normalize_yymm_value(value: object) -> str:
    text = str(value).strip().replace("-", "").replace(".", "")
    if len(text) >= 6:
        return text[:6]
    if len(text) == 4:
        return f"{text}01"
    return text


def _base_long_row(
    request: pd.Series,
    year_month: str,
    quantity: object,
    value_usd: object,
) -> dict:
    return {
        "request_id": request["request_id"],
        "event_id": request["event_id"],
        "flow_type": request["flow_type"],
        "source": request["source"],
        "regulated_country": request["regulated_country"],
        "intermediary_country": request["intermediary_country"],
        "importer_country": request["importer_country"],
        "reporter_country": request["reporter_country"],
        "partner_country": request["partner_country"],
        "hs_code": request["hs_code"],
        "year_month": year_month,
        "quantity": quantity,
        "value_usd": value_usd,
    }


def _empty_long_row(request: pd.Series, year_month: str) -> dict:
    return _base_long_row(request, year_month, quantity=0, value_usd=0)
