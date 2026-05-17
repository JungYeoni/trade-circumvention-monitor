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
