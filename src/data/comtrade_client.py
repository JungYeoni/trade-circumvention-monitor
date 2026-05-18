# src/data/comtrade_client.py
"""UN Comtrade API 데이터 수집 함수."""

import comtradeapicall
import pandas as pd

from src.config import get_comtrade_api_key

# Comtrade API 상수
MAX_RECORDS_PER_REQUEST = 250_000  # 단일 요청 최대 레코드 수


def collect_comtrade_trade(
    reporters: dict[str, str] | list[str] | str,
    partners: dict[str, str] | list[str] | str,
    hs_codes: str,
    periods: list[str] | str,
    flows: str = "M,X",
    freq_code: str = "M",
    type_code: str = "C",
    classification_code: str = "HS",
    max_records: int = MAX_RECORDS_PER_REQUEST,
    include_desc: bool = True,
) -> pd.DataFrame:
    """Collect UN Comtrade data for one or many reporter/partner countries.

    Parameters
    ----------
    reporters
        Reporter country codes. Use {"Korea": "410"}, ["410", "704"], or "all".
    partners
        Partner country codes. Use {"Russia": "643"}, ["643"], or "all".
    hs_codes
        Comma-separated HS codes, for example "7210,8542" or "TOTAL".
    periods
        Comtrade periods. Monthly example: ["202401", "202402"]. Annual example: "2020,2021".
    flows
        Comma-separated flow codes, for example "M,X".
    freq_code
        "M" for monthly or "A" for annual data.

    Returns
    -------
    pd.DataFrame
        Concatenated Comtrade response. Empty DataFrame when all requests are empty.
    """
    api_key = get_comtrade_api_key()
    reporter_map = _normalize_code_mapping(reporters, "reporters")
    partner_map = _normalize_code_mapping(partners, "partners")
    period_str = ",".join(periods) if isinstance(periods, list) else periods
    all_frames = []

    for reporter_name, reporter_code in reporter_map.items():
        for partner_name, partner_code in partner_map.items():
            print(f"Collecting Comtrade reporter={reporter_name}, partner={partner_name} ...")

            df = comtradeapicall.getFinalData(
                api_key,
                typeCode=type_code,
                freqCode=freq_code,
                clCode=classification_code,
                period=period_str,
                reporterCode=reporter_code,
                cmdCode=hs_codes,
                flowCode=flows,
                partnerCode=partner_code,
                partner2Code=None,
                customsCode=None,
                motCode=None,
                maxRecords=max_records,
                format_output="JSON",
                aggregateBy=None,
                breakdownMode="plus",
                countOnly=None,
                includeDesc=include_desc,
            )

            if df is None or not isinstance(df, pd.DataFrame) or df.empty:
                print(f"  -> no data for reporter={reporter_name}, partner={partner_name}")
                continue

            df = df.copy()
            df["reporterName"] = reporter_name
            df["partnerName"] = partner_name
            all_frames.append(df)

    if not all_frames:
        return pd.DataFrame()

    return pd.concat(all_frames, ignore_index=True)


def _normalize_code_mapping(
    values: dict[str, str] | list[str] | tuple[str, ...] | str,
    label: str,
) -> dict[str, str]:
    """Normalize one or many API codes to a {name: code} mapping."""
    if isinstance(values, dict):
        return {str(name): str(code) for name, code in values.items()}
    if isinstance(values, str):
        return {values: values}
    if isinstance(values, (list, tuple)):
        return {str(code): str(code) for code in values}
    raise TypeError(f"{label} must be a dict, list, tuple, or string.")


def _normalize_periods(periods: list[int | str] | tuple[int | str, ...] | str) -> str:
    """Convert period values to the comma-separated Comtrade API format."""
    if isinstance(periods, str):
        return periods
    return ",".join(str(period) for period in periods)


def collect_russia_trade(
    reporters: dict[str, str],
    hs_codes: str,
    years: list[int],
    flows: str = "M,X",
    partner_code: str = "643",
) -> pd.DataFrame:
    """UN Comtrade에서 대러 무역 데이터 수집.

    Parameters
    ----------
    reporters : dict[str, str]
        국가명 → Comtrade 국가코드 매핑. 예: {"Armenia": "51"}
    hs_codes : str
        쉼표로 구분된 HS 코드. 예: "7210,8542"
    years : list[int]
        수집할 연도 목록. 예: [2020, 2021, 2022, 2023, 2024]
    flows : str
        수출입 구분. "M,X" (기본값) = 수입+수출
    partner_code : str
        상대국 코드. 기본값 "643" = 러시아

    Returns
    -------
    pd.DataFrame
        수집된 원시 데이터. 실패한 국가/연도는 경고 출력 후 건너뜀.
        데이터가 없으면 빈 DataFrame 반환.
    """
    api_key = get_comtrade_api_key()
    all_list = []

    for r_name, r_code in reporters.items():
        for year in years:
            periods = [f"{year}{m:02d}" for m in range(1, 13)]
            period_str = ",".join(periods)

            print(f"Collecting {r_name} -> Russia, year {year} ...")

            df = comtradeapicall.getFinalData(
                api_key,
                typeCode="C",
                freqCode="M",
                clCode="HS",
                period=period_str,
                reporterCode=r_code,
                cmdCode=hs_codes,
                flowCode=flows,
                partnerCode=partner_code,
                partner2Code=None,
                customsCode=None,
                motCode=None,
                maxRecords=MAX_RECORDS_PER_REQUEST,
                format_output="JSON",
                aggregateBy=None,
                breakdownMode="plus",
                countOnly=None,
                includeDesc=True,
            )

            if df is None or not isinstance(df, pd.DataFrame) or df.empty:
                print(f"  -> no data or error for {r_name}, {year}")
                continue

            df = df.copy()
            df["reporterName"] = r_name
            all_list.append(df)

    if not all_list:
        return pd.DataFrame()

    return pd.concat(all_list, ignore_index=True)


def collect_comtrade_data(
    reporters: dict[str, str] | list[str] | tuple[str, ...] | str,
    partners: dict[str, str] | list[str] | tuple[str, ...] | str,
    hs_codes: str,
    periods: list[int | str] | tuple[int | str, ...] | str,
    flows: str = "M,X",
    freq_code: str = "M",
    columns: list[str] | tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """Collect UN Comtrade data for arbitrary reporter and partner countries.

    Parameters
    ----------
    reporters
        Reporter country codes. A dict keeps readable names, e.g.
        ``{"Korea": "410", "China": "156"}``; a list/string uses the code as
        both name and code.
    partners
        Partner country codes. Same format as ``reporters``.
    hs_codes
        Comma-separated HS codes, e.g. ``"7210,8542"`` or ``"TOTAL"``.
    periods
        Comtrade periods. For monthly data use ``"202401,202402"`` or a list.
        For annual data use ``freq_code="A"`` and values like ``["2022"]``.
    flows
        Flow code sent to Comtrade. Common values are ``"M"``, ``"X"``, or
        ``"M,X"``.
    freq_code
        Comtrade frequency code. ``"M"`` for monthly, ``"A"`` for annual.
    columns
        Optional columns to keep in the returned DataFrame. Helper columns
        ``reporterName`` and ``partnerName`` are included when requested.

    Returns
    -------
    pd.DataFrame
        Concatenated Comtrade responses. Empty responses are skipped; if every
        request is empty, returns an empty DataFrame.
    """
    api_key = get_comtrade_api_key()
    reporter_map = _normalize_code_mapping(reporters, "reporters")
    partner_map = _normalize_code_mapping(partners, "partners")
    period_str = _normalize_periods(periods)
    all_list = []

    for reporter_name, reporter_code in reporter_map.items():
        for partner_name, partner_code in partner_map.items():
            print(
                "Collecting Comtrade "
                f"reporter={reporter_name} partner={partner_name} "
                f"hs={hs_codes} periods={period_str} flows={flows} ..."
            )

            df = comtradeapicall.getFinalData(
                api_key,
                typeCode="C",
                freqCode=freq_code,
                clCode="HS",
                period=period_str,
                reporterCode=reporter_code,
                cmdCode=hs_codes,
                flowCode=flows,
                partnerCode=partner_code,
                partner2Code=None,
                customsCode=None,
                motCode=None,
                maxRecords=MAX_RECORDS_PER_REQUEST,
                format_output="JSON",
                aggregateBy=None,
                breakdownMode="plus",
                countOnly=None,
                includeDesc=True,
            )

            if df is None or not isinstance(df, pd.DataFrame) or df.empty:
                print(f"  -> no data or error for {reporter_name}, {partner_name}")
                continue

            df = df.copy()
            df["reporterName"] = reporter_name
            df["partnerName"] = partner_name
            all_list.append(df)

    if not all_list:
        return pd.DataFrame(columns=list(columns) if columns is not None else None)

    result = pd.concat(all_list, ignore_index=True)
    if columns is not None:
        for col in columns:
            if col not in result.columns:
                result[col] = pd.NA
        result = result[list(columns)]

    return result
