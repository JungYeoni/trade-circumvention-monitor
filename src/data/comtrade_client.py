# src/data/comtrade_client.py
"""UN Comtrade API 데이터 수집 함수."""

import comtradeapicall
import pandas as pd

from src.config import get_comtrade_api_key

# Comtrade API 상수
MAX_RECORDS_PER_REQUEST = 250_000  # 단일 요청 최대 레코드 수


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
