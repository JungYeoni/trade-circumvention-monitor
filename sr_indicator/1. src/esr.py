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

# 선적·통관·재수출 과정의 시간 지연을 고려해 0~3개월 시차를 모두 계산
DEFAULT_ESR_LAGS = (0, 1, 2, 3)
DEFAULT_IMPORTER_COUNTRY = "대한민국"

# ISR 결과에서 ESR 후보 쌍을 추릴 때 필요한 컬럼
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

# wide 형태 ESR 입력 데이터셋 컬럼 (1행 = 규제국-중간국-수입국 삼각형의 1개월)
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

# ESR 점수 계산 결과 컬럼 (lag별 상관계수 + 위험도 요약)
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
    """ISR 결과에서 ESR 분석 대상 쌍을 필터링한다.

    ISR에서 음의 상관(수입 전이 의심)이 나온 쌍만 ESR로 넘겨
    불필요한 API 호출을 줄인다.

    By default, non-positive ``sr_min`` rows are selected because those match the
    import-shift direction: regulated-country imports fall while intermediary-country
    imports rise.
    """
    missing = set(ESR_PAIR_COLUMNS) - set(isr_result_df.columns)
    if missing:
        raise ValueError(f"ISR 결과 데이터에 필수 컬럼이 없습니다: {sorted(missing)}")

    pairs = isr_result_df[ESR_PAIR_COLUMNS].copy()
    # sr_min <= 0: 규제국 수입 감소와 후보국 수입 증가가 음의 상관인 쌍만 선택
    pairs = pairs[pairs["sr_min"] <= max_isr_min]

    if min_isr_risk is not None:
        pairs = pairs[pairs["sr_risk"] >= min_isr_risk]

    # 위험도 높은 순, 동점이면 상관계수 낮은 순으로 정렬
    pairs = pairs.sort_values(["sr_risk", "sr_min"], ascending=[False, True])
    if top_n is not None:
        pairs = pairs.head(top_n)

    return pairs.reset_index(drop=True)


def make_esr_country_code_template(
    isr_pairs: pd.DataFrame,
    importer_country: str = DEFAULT_IMPORTER_COUNTRY,
) -> pd.DataFrame:
    """Comtrade API 호출에 필요한 국가코드 매핑 템플릿을 생성한다.

    Comtrade API는 국가명 대신 숫자 코드를 요구하므로,
    이 함수로 빈 템플릿을 만들고 사람이 직접 코드를 채운 뒤 다음 단계로 넘긴다.
    """
    # ISR 쌍의 규제국·후보국과 수입국(대한민국)을 모두 모아 유니크 목록 생성
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
            "comtrade_country_code": "",  # 사람이 직접 채워야 하는 컬럼
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
    """ISR 쌍 1개당 Comtrade API 요청 2건을 담은 수집 계획을 만든다.

    쌍 1개 → 2행 생성:
      - regulated_to_intermediary: 규제국 -> 중간국 수출
      - regulated_to_importer:     규제국 -> 수입국 수출

    The output has two rows per ISR pair:
    ``regulated_to_intermediary`` for 규제국 -> 중간국 and
    ``regulated_to_importer`` for 규제국 -> 수입국.
    """
    required_map_cols = {"country_name_kr", "comtrade_country_code"}
    missing_map_cols = required_map_cols - set(country_code_map.columns)
    if missing_map_cols:
        raise ValueError(f"국가코드 매핑에 필수 컬럼이 없습니다: {sorted(missing_map_cols)}")

    map_df = country_code_map.dropna(subset=["country_name_kr"]).copy()
    # reporter_code/partner_code가 없으면 comtrade_country_code로 대체
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

        # 국가코드 매핑이 없으면 해당 쌍은 건너뜀
        if not regulated_code or regulated_code.lower() == "nan":
            continue
        if not intermediary_code or intermediary_code.lower() == "nan":
            continue

        # lag 적용을 위해 window + max(lags)개월치 기간을 수집
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
            "flow_code": "X",  # X = 수출
            "isr_min": row.get("sr_min"),
            "isr_best_lag": row.get("sr_best_lag"),
            "isr_risk": row.get("sr_risk"),
        }
        # 규제국 -> 중간국 수출 요청
        rows.append(
            {
                **base,
                "flow_type": "regulated_to_intermediary",
                "partner_code": intermediary_code,
                "partner_country": intermediary_country,
            }
        )
        # 규제국 -> 수입국(한국) 수출 요청
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
    """이미 수집된 두 수출 흐름 테이블을 합쳐 wide 형태 ESR 입력 데이터를 만든다.

    collect_esr_export_flow_dataset으로 API를 직접 호출하는 대신,
    기존에 저장된 CSV 데이터를 활용할 때 사용한다.

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
    # 각 흐름 테이블의 컬럼명을 접두사 붙인 형태로 표준화하고 단가 파생
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

    # outer join: 한쪽 흐름에만 데이터가 있는 월도 보존
    key_cols = ["사건번호", "품목", "hs_code", "년월", "규제국", "중간국"]
    esr_df = left.merge(right, on=key_cols, how="outer")

    # ISR 메타 정보(sr_min 등)를 isr_* 접두사로 붙임
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

    # 누락 컬럼을 NaN으로 채워 스키마를 통일
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
    """wide 삼각형 데이터에서 lag별 ESR 점수를 계산한다.

    ESR = Spearman(규제국→수입국 수출량, 규제국→중간국 수출량[lag 이동])
    음수일수록 수출 전환 의심도 높음 (한국 수출 감소 + 중간국 수출 증가 동시 발생)

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
    # YYYY.MM 형식 아닌 행 제거
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
        # lag 이동분까지 포함한 전체 월 범위로 reindex (결측 월은 0으로 채움)
        full_months = pd.date_range(start=start_month, periods=window + max(sorted_lags), freq="MS")

        monthly = (
            group.set_index("년월_dt")[
                ["규제국_중간국_수출량", "규제국_수입국_수출량"]
            ]
            .reindex(full_months)
            .fillna(0)
        )

        # 수입국(한국) 수출 시계열: 분석 window 기간
        importer_series = monthly["규제국_수입국_수출량"].iloc[:window].reset_index(drop=True)
        intermediary_full = monthly["규제국_중간국_수출량"]

        # 수입국 수출이 모두 같은 값이거나 중간국 수출이 0이면 상관 계산 불가 → 건너뜀
        if importer_series.nunique() <= 1 or intermediary_full.sum() <= min_total_export:
            continue

        esr_by_lag: dict[str, float] = {}
        for lag in sorted_lags:
            # 중간국 수출 시계열을 lag만큼 밀어서 수입국 시계열과 비교
            intermediary_series = intermediary_full.iloc[lag : lag + window].reset_index(drop=True)
            if len(intermediary_series) < window or intermediary_series.nunique() <= 1:
                esr_by_lag[f"esr_lag{lag}"] = np.nan
                continue

            esr_value, _ = spearmanr(importer_series, intermediary_series)
            esr_by_lag[f"esr_lag{lag}"] = esr_value

        # 유효한 lag 중 가장 낮은(가장 음수인) 상관계수를 최종 ESR로 채택
        valid_esrs = {
            lag: esr_by_lag.get(f"esr_lag{lag}")
            for lag in sorted_lags
            if pd.notna(esr_by_lag.get(f"esr_lag{lag}"))
        }
        if valid_esrs:
            esr_best_lag = min(valid_esrs, key=valid_esrs.get)
            esr_min = valid_esrs[esr_best_lag]
            # esr_risk: 음수 상관을 0~1 위험도로 변환 (양수 상관은 0으로 클리핑)
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
                "규제국_중간국_수출합": intermediary_full.sum(),
                "규제국_수입국_수출합": importer_series.sum(),
            }
        )

    return pd.DataFrame(results)


def collect_esr_export_flow_dataset(
    collection_plan: pd.DataFrame,
    max_requests: int | None = None,
    max_records: int = 250_000,
) -> pd.DataFrame:
    """수집 계획에 따라 Comtrade API를 호출하고 wide ESR 입력 데이터셋을 반환한다.

    내부 흐름:
      수집 계획 행마다 API 호출
        → _comtrade_response_to_esr_rows 로 월별 행 변환 (long 형태)
      전체 long 행 모음
        → _wide_esr_dataset_from_long_rows 로 wide 변환

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
    """수출 흐름 테이블의 컬럼명을 접두사 형태로 표준화하고 단가를 파생한다.

    수출량이 0인 행은 단가를 NaN으로 처리해 0 나눗셈을 방지한다.
    """
    required = {"사건번호", "품목", "hs_code", "년월", "규제국", "중간국", "수출량", "수출총달러"}
    missing = required - set(export_df.columns)
    if missing:
        raise ValueError(f"수출 흐름 데이터에 필수 컬럼이 없습니다: {sorted(missing)}")

    df = export_df.copy()
    df[quantity_col] = pd.to_numeric(df["수출량"], errors="coerce").fillna(0)
    df[value_col] = pd.to_numeric(df["수출총달러"], errors="coerce").fillna(0)
    # 수출량 > 0인 경우에만 단가 계산, 0이면 NaN
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
    """Comtrade API 응답 1건을 월별 행 리스트(long 형태)로 변환한다.

    수집 계획의 모든 기간을 먼저 0으로 초기화한 뒤,
    API 응답이 있는 월만 실제 값으로 덮어쓴다.
    API 실패·결측 월은 자동으로 0으로 남는다.
    """
    periods = str(request["periods"]).split(",")
    # 수집 대상 전 기간을 0으로 초기화 (API 결측 월 보호)
    monthly = {period: {"수출량": 0.0, "수출총달러": 0.0} for period in periods}

    if response_df is not None and isinstance(response_df, pd.DataFrame) and not response_df.empty:
        df = response_df.copy()
        # 기간 컬럼 확인: period 컬럼이 없으면 refYear + refMonth로 조합
        period_col = "period" if "period" in df.columns else None
        if period_col is None and {"refYear", "refMonth"}.issubset(df.columns):
            df["period"] = (
                df["refYear"].astype(int).astype(str)
                + df["refMonth"].astype(int).astype(str).str.zfill(2)
            )
            period_col = "period"

        if period_col is not None:
            value_col = "primaryValue" if "primaryValue" in df.columns else None
            # 수출량으로 쓸 컬럼을 우선순위대로 선택 (netWgt > qty > altQty > grossWgt)
            quantity_col = _choose_comtrade_quantity_col(df)
            grouped = df.groupby(period_col, dropna=False).agg(
                수출총달러=(value_col, "sum") if value_col else (df.columns[0], "size"),
                # TODO: quantity_col=None 이면 행 수(size)가 수출량으로 잘못 저장됨 → 0 처리 필요
                수출량=(quantity_col, "sum") if quantity_col else (df.columns[0], "size"),
            )
            for period, values in grouped.iterrows():
                period_key = str(period)
                # float 형태로 넘어온 기간 키 정규화 (예: "202201.0" → "202201")
                if period_key.endswith(".0"):
                    period_key = period_key[:-2]
                if period_key in monthly:
                    monthly[period_key]["수출량"] = float(values["수출량"])
                    monthly[period_key]["수출총달러"] = float(values["수출총달러"])

    # 월별 딕셔너리를 메타 정보와 결합해 행 리스트로 변환
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
    """API 응답에서 수출량 컬럼을 우선순위대로 선택한다.

    우선순위: netWgt(순중량) > qty(신고수량) > altQty(대체수량) > grossWgt(총중량)
    해당 컬럼이 없으면 None 반환 → 호출부에서 별도 처리 필요
    """
    for col in ["netWgt", "qty", "altQty", "grossWgt"]:
        if col in df.columns:
            return col
    return None


def _wide_esr_dataset_from_long_rows(long_df: pd.DataFrame) -> pd.DataFrame:
    """flow_type 컬럼으로 구분된 long 형태를 wide 형태로 변환한다.

    long 형태 (flow_type 컬럼으로 구분):
      regulated_to_intermediary 행 + regulated_to_importer 행

    wide 형태 (1행 = 1개월):
      규제국_중간국_수출량 | 규제국_수입국_수출량 | ...
    """
    key_cols = ["사건번호", "품목", "hs_code", "년월", "규제국", "중간국", "수입국"]
    meta_cols = ["isr_min", "isr_best_lag", "isr_risk"]

    # flow_type별로 분리해 컬럼명에 접두사를 붙인 뒤 wide로 병합
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
    # ISR 메타 정보 합류 (중복 제거 후 left join)
    meta = long_df[key_cols + meta_cols].drop_duplicates(key_cols)
    esr_df = esr_df.merge(meta, on=key_cols, how="left")

    # 수출량·금액 타입 정규화 및 단가 파생
    for prefix in ["규제국_중간국", "규제국_수입국"]:
        qty_col = f"{prefix}_수출량"
        value_col = f"{prefix}_수출총달러"
        unit_col = f"{prefix}_단가"
        esr_df[qty_col] = pd.to_numeric(esr_df[qty_col], errors="coerce").fillna(0)
        esr_df[value_col] = pd.to_numeric(esr_df[value_col], errors="coerce").fillna(0)
        esr_df[unit_col] = np.where(esr_df[qty_col] > 0, esr_df[value_col] / esr_df[qty_col], np.nan)

    # 누락 컬럼을 NaN으로 채워 스키마 통일
    for col in ESR_DATASET_COLUMNS:
        if col not in esr_df.columns:
            esr_df[col] = np.nan

    return esr_df[ESR_DATASET_COLUMNS].sort_values(
        ["사건번호", "품목", "hs_code", "규제국", "중간국", "년월"]
    ).reset_index(drop=True)


def _monthly_periods(start_yymm_dot: str, months: int) -> list[str]:
    """시작 월(YYYY.MM)부터 months개월치 기간을 YYYYMM 문자열 리스트로 반환한다.

    Comtrade API의 period 파라미터 형식(YYYYMM)에 맞춘다.
    예) _monthly_periods("2022.01", 3) → ["202201", "202202", "202203"]
    """
    start = pd.to_datetime(str(start_yymm_dot), format="%Y.%m")
    return [period.strftime("%Y%m") for period in pd.date_range(start=start, periods=months, freq="MS")]


def save_esr_dataset(esr_df: pd.DataFrame, path: str) -> None:
    """ESR 데이터셋을 UTF-8 BOM CSV로 저장한다.

    utf-8-sig 인코딩은 한글 컬럼명이 Excel에서 깨지지 않도록 BOM을 포함한다.
    """
    esr_df.to_csv(path, index=False, encoding="utf-8-sig")
