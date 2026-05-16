"""Korea Customs item-by-country trade API collection utilities."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime

import pandas as pd
import requests

from src.config import get_customs_api_key

CUSTOMS_NITEM_TRADE_URL = "https://apis.data.go.kr/1220000/nitemtrade/getNitemtradeList"
DEFAULT_CUSTOMS_COLUMNS = [
    "year",
    "statCdCntnKor1",
    "statCd",
    "statKor",
    "hsCd",
    "impDlr",
    "expDlr",
    "impWgt",
    "expWgt",
    "balPayments",
]
NUMERIC_CUSTOMS_COLUMNS = {"impDlr", "expDlr", "impWgt", "expWgt", "balPayments"}


def _validate_yymm(yymm: str) -> None:
    try:
        datetime.strptime(yymm, "%Y%m")
    except ValueError as exc:
        raise ValueError(f"Invalid date format: {yymm}. Use YYYYMM.") from exc


def _add_months(dt: datetime, months: int) -> datetime:
    year = dt.year + (dt.month - 1 + months) // 12
    month = (dt.month - 1 + months) % 12 + 1
    return dt.replace(year=year, month=month)


def split_yymm_period(start: str, end: str, max_months: int = 12) -> list[tuple[str, str]]:
    """Split an inclusive YYYYMM period into API-safe chunks."""
    _validate_yymm(start)
    _validate_yymm(end)
    start_dt = datetime.strptime(start, "%Y%m")
    end_dt = datetime.strptime(end, "%Y%m")

    if start_dt > end_dt:
        raise ValueError("start cannot be later than end.")
    if max_months < 1:
        raise ValueError("max_months must be at least 1.")

    periods = []
    current_start = start_dt
    while current_start <= end_dt:
        current_end = _add_months(current_start, max_months - 1)
        if current_end > end_dt:
            current_end = end_dt
        periods.append((current_start.strftime("%Y%m"), current_end.strftime("%Y%m")))
        current_start = _add_months(current_end, 1)

    return periods


def _normalize_country_mapping(countries: dict[str, str] | list[str] | str) -> dict[str, str]:
    if isinstance(countries, dict):
        return countries
    if isinstance(countries, str):
        return {countries: countries}
    if isinstance(countries, list):
        return {str(country): str(country) for country in countries}
    raise TypeError("countries must be a dict, list, or string.")


def collect_customs_trade(
    start: str,
    end: str,
    hs_code: str,
    countries: dict[str, str] | list[str] | str,
    columns: list[str] | None = None,
    rename_map: dict[str, str] | None = None,
    exclude_total: bool = True,
    max_months_per_request: int = 12,
    timeout: int = 30,
) -> pd.DataFrame:
    """Collect Korea Customs item-by-country import/export data.

    Parameters
    ----------
    start, end
        Inclusive query period in YYYYMM format.
    hs_code
        HS code sent as ``hsSgn``.
    countries
        Country code(s) sent as ``cntyCd``. Use {"United States": "US"}, ["US"], or "US".
    columns
        XML item tags to keep. Defaults to the columns used in the GW notebook.
    rename_map
        Optional DataFrame column rename mapping.
    exclude_total
        Whether to drop rows whose ``year`` value is the API total row.
    max_months_per_request
        The API is queried in chunks; default is 12 inclusive months per request.

    Returns
    -------
    pd.DataFrame
        Concatenated customs trade data for all requested countries and periods.
    """
    service_key = get_customs_api_key()
    columns = columns or DEFAULT_CUSTOMS_COLUMNS
    rename_map = rename_map or {}
    country_map = _normalize_country_mapping(countries)
    all_rows = []

    for country_name, country_code in country_map.items():
        for period_start, period_end in split_yymm_period(start, end, max_months_per_request):
            params = {
                "serviceKey": service_key,
                "strtYymm": period_start,
                "endYymm": period_end,
                "hsSgn": hs_code,
                "cntyCd": country_code,
            }
            response = requests.get(CUSTOMS_NITEM_TRADE_URL, params=params, timeout=timeout)

            if response.status_code != 200:
                raise RuntimeError(
                    f"Customs API HTTP error: {response.status_code}\n"
                    f"Response: {response.text[:300]}"
                )

            try:
                root = ET.fromstring(response.text)
            except ET.ParseError as exc:
                raise RuntimeError(f"Customs API XML parse failed: {response.text[:300]}") from exc

            result_code = root.findtext("./header/resultCode")
            result_msg = root.findtext("./header/resultMsg")
            if result_code != "00":
                raise RuntimeError(
                    f"Customs API error: resultCode={result_code}, resultMsg={result_msg}"
                )

            for item in root.findall("./body/items/item"):
                if exclude_total and item.findtext("year") == "총계":
                    continue

                row = {
                    "query_country_name": country_name,
                    "query_country_code": country_code,
                    "query_start_yymm": period_start,
                    "query_end_yymm": period_end,
                }
                for col in columns:
                    value = item.findtext(col)
                    if col in NUMERIC_CUSTOMS_COLUMNS and value not in (None, "", "-"):
                        try:
                            value = int(value)
                        except ValueError:
                            pass
                    row[col] = value
                all_rows.append(row)

    df = pd.DataFrame(all_rows)
    if rename_map:
        df = df.rename(columns=rename_map)
    return df
