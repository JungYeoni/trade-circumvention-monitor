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

"""Korea Customs trade API collection helpers."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
import requests

from src.config import get_customs_api_key

DEFAULT_CUSTOMS_API_URL = "https://apis.data.go.kr/1220000/nitemtrade/getNitemtradeList"


def _normalize_country_mapping(
    countries: dict[str, str] | list[str] | tuple[str, ...] | str,
) -> dict[str, str]:
    """Normalize one or many customs country codes to a {name: code} mapping."""
    if isinstance(countries, dict):
        return {str(name): str(code) for name, code in countries.items()}
    if isinstance(countries, str):
        return {countries: countries}
    if isinstance(countries, (list, tuple)):
        return {str(code): str(code) for code in countries}
    raise TypeError("countries must be a dict, list, tuple, or string.")


def split_yymm_period(start_yymm: str, end_yymm: str) -> list[tuple[str, str]]:
    """Split YYYYMM periods into one request per calendar year."""
    start = pd.Period(start_yymm, freq="M")
    end = pd.Period(end_yymm, freq="M")
    if end < start:
        raise ValueError("end_yymm must be greater than or equal to start_yymm.")

    ranges = []
    current = start
    while current <= end:
        year_end = pd.Period(f"{current.year}12", freq="M")
        chunk_end = min(year_end, end)
        ranges.append((current.strftime("%Y%m"), chunk_end.strftime("%Y%m")))
        current = chunk_end + 1
    return ranges


def collect_customs_trade(
    hs_code: str,
    countries: dict[str, str] | list[str] | tuple[str, ...] | str,
    start_yymm: str,
    end_yymm: str,
    direction: str = "import",
    api_url: str = DEFAULT_CUSTOMS_API_URL,
    columns: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Collect Korea Customs monthly trade data by HS code and country.

    ``direction="import"`` is used for country -> Korea flows. ``direction="export"``
    can be used for Korea -> country flows if needed later.
    """
    service_key = get_customs_api_key()
    country_map = _normalize_country_mapping(countries)
    all_frames = []

    for country_name, country_code in country_map.items():
        for start, end in split_yymm_period(start_yymm, end_yymm):
            params = {
                "serviceKey": service_key,
                "strtYymm": start,
                "endYymm": end,
                "hsSgn": str(hs_code),
                "cntyCd": str(country_code),
                "type": "json",
            }
            response = requests.get(api_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            items = _extract_customs_items(data)
            if not items:
                continue

            frame = pd.DataFrame(items)
            frame["countryName"] = country_name
            frame["countryCode"] = str(country_code)
            frame["tradeDirection"] = direction
            all_frames.append(frame)

    if not all_frames:
        return pd.DataFrame(columns=list(columns) if columns is not None else None)

    result = pd.concat(all_frames, ignore_index=True)
    if columns is not None:
        for col in columns:
            if col not in result.columns:
                result[col] = pd.NA
        result = result[list(columns)]
    return result


def _extract_customs_items(data: dict) -> list[dict]:
    body = data.get("response", {}).get("body", {})
    items = body.get("items", {})
    item = items.get("item", []) if isinstance(items, dict) else items
    if isinstance(item, dict):
        return [item]
    if isinstance(item, list):
        return item
    return []
