# 노트북 06-10 검증 리뷰

검증일: 2026-05-27

최신 재리뷰: 2026-05-27 (v6 — 방법론 한계: 대조군 부재와 공급망 재편 대안 설명 추가)

## 검토 대상

- `notebooks/06_customs_flow0_flow2_collection.ipynb`
- `notebooks/07_flow0_flow2_analysis.ipynb`
- `notebooks/08_comtrade_flow1_collection.ipynb`
- `notebooks/09_triangular_trade_analysis.ipynb`
- `notebooks/10_price_volume_decomposition.ipynb` (구 `10_comtrade_world_price_collection.ipynb` → 방향 전환 후 삭제)

## 요약

노트북 06-09는 반덤핑 규제 우회 가능성과 일관된 1-hop 삼각무역 패턴을 탐색하는 파이프라인이고, 노트북 10은 의심 케이스의 금액 증가가 물량 때문인지 가격 상승 때문인지 분해하는 노트북이다. (구 10번 목적이었던 World→World Comtrade 단가 수집은 API 응답 문제로 deprecated 후 삭제)

- `flow0`: 규제국 -> 한국 직접 수입
- `flow1`: 규제국 -> 중간국 수출
- `flow2`: 중간국 -> 한국 수입

해석 범위는 명확히 제한해야 한다. 현재 분석은 대조군 없는 before/after 기반 스크리닝이며, 통계적 유의성 검정이나 인과 추정이 아니다. 따라서 결과는 "우회 확정"이 아니라 "추가 검토가 필요한 1-hop 우회 의심 후보"로 해석해야 한다. 특히 중국 -> 베트남 조합처럼 글로벌 공급망 재편과 우회무역이 관측상 비슷하게 나타날 수 있는 케이스는 대안 설명을 반드시 병기해야 한다.

초기 재검증 결과, 최종 의심 케이스 산출에 직접 영향을 주는 주요 문제는 네 가지였다.

1. `06`에서 flow0/flow2를 사건 단위가 아니라 HS/window 묶음 단위로 분류해 일부 사건의 flow0에 다른 사건의 규제국이 섞인다.
2. `07`에서 flow0 월평균이라고 설명한 값이 실제로는 before/after 기간 총합이다.
3. `07`과 `08`에서 flow2 후보국 집계가 월별 합산 후 평균이 아니라 raw row 평균이다.
4. `09`의 최종 삼각무역 분석이 before/after 총합 비교를 사용해 월 수 불균형에 취약하며, 월평균 기준으로 바꾸면 의심 케이스가 달라진다.

추가로 `08`에서는 대만(`TWN`)의 Comtrade reporter 코드 매핑 실패로 TWN 관련 flow1이 누락되어 있었다.

v3 재리뷰에서 추가 발견된 문제:

5. `09` dedup 키에 `hs_code`(10자리)가 없어 동일 월·국가의 HS 세부코드 row가 첫 번째만 남고 나머지가 버려져 flow2 금액이 과소계산되었다. (→ 해결)

v4 재리뷰에서 추가 발견된 문제:

6. `customs_flow0_flow2_raw.csv`와 customs parquet cache의 `trade_date`가 float 형태로 저장되어 `2020.10` 같은 10월 값이 `2020.1`로 손실된다. 이후 `pd.to_datetime(..., format="%Y.%m")`가 이를 1월로 파싱해 07/09/10의 before/after 월 판정이 틀어질 수 있다.

최신 재리뷰 기준 상태는 다음과 같다.

| 항목                         | 최신 상태                                                                              | 판단                                     |
| ---------------------------- | -------------------------------------------------------------------------------------- | ---------------------------------------- |
| `09` flow 재분류             | `flow_corrected` 도입 확인                                                             | 해결                                     |
| `09` before/after 집계       | 월별 합산 후 월평균 방식 확인                                                          | 해결                                     |
| `07`/`08` flow2 raw-row mean | 월별 합산 후 월평균 방식 확인                                                          | 해결                                     |
| `08` TWN reporter 매핑       | `TWN -> 490` 수동 매핑 및 TWN flow1 1,000행 확인                                       | 해결                                     |
| `08` API 키 앞자리 출력      | `API_KEY[:8]`, `새 키 적용` 문자열 검색 결과 없음                                      | 해결                                     |
| `09` hs_code dedup 누락      | `dedup_keys`에 `hs_code` 추가 → 의심 조합 34건→**43건** (23개 사건, trade_date 수정 후) | 해결                                   |
| `10` 가격·물량 분해          | trade_date 수정 후 재실행 완료, 43건 / f2_pct≈dlr_pct 43/43 정합                       | 해결                                   |
| `10` 세계 단가 수집          | `World -> World` 응답 0/NaN 문제 확인, 구 노트북 삭제 후 신규 노트북으로 대체           | 해결 (방향 전환)                        |
| customs `trade_date`         | cache float 변환 + CSV 재생성 완료, 07/09/10 파싱 `%Y-%m`으로 수정                     | 해결                                   |
| `08` 후보국 선정 기준        | 여전히 기존 `flow == 2` 기준 사용                                                      | 미해결 (우선순위 medium)                 |
| `07` 분석 기준               | 여전히 기존 `flow` 기준 사용                                                           | 미해결 또는 보정 전 탐색용으로 명시 필요 |

주요 이슈(Issue 5.4 trade_date)는 해결되었다. cache float 변환과 CSV 재생성, 07/09/10 파싱 포맷 수정, 재실행 후 f2_pct≈dlr_pct 43/43 정합 확인까지 완료했다. trade_date 수정 결과 의심 사건이 25개 → 23개로 소폭 감소(2개 탈락)했고 suspicion_score도 변동했다.

잔여 이슈는 `08`에서 flow1 수집 후보국을 고를 때 `flow_corrected` 기준을 사용하지 않는다는 점이다(Issue 5.1). 이 때문에 corrected flow2로 편입되는 22개 조합에 flow1 데이터가 없다. 이 22개 조합은 현재 상위 의심 케이스에 포함되지 않아 우선순위는 medium이다.

## 1. `06`: flow0 분류에 다른 사건의 규제국이 섞임

### 위치

- API 호출 키 생성: `notebooks/06_customs_flow0_flow2_collection.ipynb`
  - `(hs_code, window_start, window_end)` 기준 groupby
  - `regulated_iso3s=("origin_country_iso3", list)`
- flow 분류:
  - 각 수집 row의 `country_iso2`가 `regulated_iso3s`에 포함되면 `flow=0`
- 메타 병합:
  - `df_raw.merge(df_meta, on=["hs_code_query", "window_start", "window_end"], how="left")`

### 확인 결과

원자화 데이터 기준:

- 전체 고유 `(hs_code, window_start, window_end)` 조합: 84개
- 여러 규제국이 섞인 조합: 40개
- 여러 `source_row_id`가 섞인 조합: 5개

flow0 국가가 원래 사건의 규제국보다 많이 들어간 명백한 오분류가 확인된 `source_row_id`는 13개다.

| source_row_id | 원래 규제국 | 실제 flow0 국가 | 문제                   |
| ------------: | ----------- | --------------- | ---------------------- |
|             5 | CN, JP, SG  | CN, IN, JP, SG  | IN이 잘못 포함         |
|             6 | IN          | CN, IN, JP, SG  | CN, JP, SG가 잘못 포함 |
|            11 | MY          | CN, MY          | CN이 잘못 포함         |
|            12 | CN          | CN, MY          | MY가 잘못 포함         |
|            23 | CN, JP, SG  | CN, IN, JP, SG  | IN이 잘못 포함         |
|            24 | IN          | CN, IN, JP, SG  | CN, JP, SG가 잘못 포함 |
|            30 | MY          | CN, MY, VN      | CN, VN이 잘못 포함     |
|            31 | CN          | CN, MY, VN      | MY, VN이 잘못 포함     |
|            32 | VN          | CN, MY, VN      | CN, MY가 잘못 포함     |
|            50 | CN          | CN, MY, VN      | MY, VN이 잘못 포함     |
|            52 | MY          | CN, MY, VN      | CN, VN이 잘못 포함     |
|            53 | VN          | CN, MY, VN      | CN, MY가 잘못 포함     |

### 상세 사유

flow0의 정의는 "해당 규제 사건의 규제국 -> 한국"이다. 따라서 분류 기준은 개별 사건 또는 최소한 개별 `source_row_id`의 규제국이어야 한다.

현재 로직은 API 호출량을 줄이기 위해 같은 HS코드와 같은 window를 하나로 묶는다. 이 자체는 캐시/수집 최적화로는 가능하지만, flow 분류까지 그 묶음의 전체 규제국 목록으로 수행하면 의미가 바뀐다.

예를 들어 같은 HS코드와 같은 기간에 중국 사건과 말레이시아 사건이 같이 있으면, 중국 사건의 flow0에 말레이시아 수입이 들어가고 말레이시아 사건의 flow0에 중국 수입이 들어간다.

### 영향

- `07`의 flow0 감소율이 사건별 직접수입 감소율이 아니게 된다.
- `09`의 `f0_pct < 0` 조건이 잘못 판정될 수 있다.
- 최종 `circumvention_suspects.csv`의 의심 여부와 순위가 바뀔 수 있다.

### 보완 방향

수집 캐시는 `(hs_code, window_start, window_end)` 단위로 유지하더라도, flow 분류는 메타 병합 후 각 `source_row_id` 또는 `event_id`의 규제국 기준으로 다시 수행해야 한다.

권장 순서:

1. API raw 결과에는 `flow`를 붙이지 않는다.
2. raw 결과를 `df_meta`와 병합해 사건별 row로 확장한다.
3. 각 row의 `origin_country_iso3` 또는 source별 규제국 집합을 ISO2로 변환한다.
4. 해당 사건 기준으로 `country_iso2`가 규제국이면 `flow=0`, 아니면 `flow=2`로 분류한다.

### 최신 상태

`09_triangular_trade_analysis.ipynb`에는 source-level 규제국 집합 기준 `flow_corrected`가 도입되었다. 재검산 결과 corrected flow0에는 다른 사건의 규제국이 추가로 섞이는 문제가 없었다.

다만 `08_comtrade_flow1_collection.ipynb`와 `07_flow0_flow2_analysis.ipynb`는 아직 기존 `flow` 컬럼을 사용하는 지점이 남아 있다. 따라서 `09`의 최종 분석 로직만 보정된 상태이며, flow1 수집 후보 생성과 07 탐색 분석은 같은 기준으로 맞춰야 한다.

## 2. `07`: flow0 월평균 계산이 실제로는 기간 총합

### 위치

`notebooks/07_flow0_flow2_analysis.ipynb`의 flow0 집계 셀.

주석은 `source_row_id x trade_date x period_label` 기준 월별 집계라고 설명하지만 실제 groupby는 다음 형태다.

```python
.groupby(["source_row_id", "product_name_kr", "period_label"])
```

`trade_date`가 groupby에 없기 때문에 before 전체 기간과 after 전체 기간의 합계가 만들어진다.

### 확인 결과

현재 notebook 방식의 after 값은 정상적인 월평균 대비 대부분 12배 수준이다. 월 수가 before/after에서 같으면 증감률은 우연히 비슷할 수 있지만, 월 수가 다르면 증감률까지 바뀐다.

대표 차이:

| source_row_id | 품목                                     | 현재 총합 기준 변화율 | 월평균 기준 변화율 |    차이 |
| ------------: | ---------------------------------------- | --------------------: | -----------------: | ------: |
|            62 | 차아황산소다                             |                -45.7% |             +19.4% | -65.1%p |
|            60 | 탄소강과 그밖의 합금강 열간압연 후판제품 |                -39.1% |             +11.6% | -50.7%p |
|            58 | 석유수지                                 |                -33.7% |              -0.6% | -33.1%p |
|            61 | 파티클보드                               |                -84.3% |             -65.4% | -18.9%p |
|            59 | 스테인리스스틸 후판                      |                -77.0% |             -60.6% | -16.4%p |

### 상세 사유

분석 목적은 규제 전후 수입 강도의 변화다. 이 경우 비교 단위는 월평균, 같은 개월 수의 합계, 또는 계절 보정된 월별 지표여야 한다.

하지만 현재 방식은 관측 기간의 총합을 비교한다. before가 11개월이고 after가 12개월이면 after가 구조적으로 크게 보인다. 반대로 최근 사건처럼 after 관측 개월 수가 적으면 after가 구조적으로 작게 보인다.

### 영향

- flow0 감소 여부가 잘못 판정될 수 있다.
- `07`의 우회 의심 사건 목록과 `suspicion_score`가 왜곡된다.
- `09`와 결합할 때 최종 의심 조건의 첫 번째 조건인 `f0_pct < 0`에 영향을 준다.

### 보완 방향

flow0은 다음 순서로 집계해야 한다.

1. `source_row_id, trade_date, period_label` 기준으로 규제국 수입액을 합산한다.
2. `source_row_id, period_label` 기준으로 월평균을 계산한다.
3. before/after 월평균을 비교한다.

### 최신 상태

`07_flow0_flow2_analysis.ipynb`의 flow0 집계는 `source_row_id, product_name_kr, trade_date, period_label` 기준 월별 합산 후 월평균 방식으로 수정되었다. 총합을 월평균으로 오인하던 문제는 해결된 것으로 판단한다.

단, 이 집계는 아직 기존 `flow` 컬럼을 사용한다. 따라서 flow0/flow2 분류 오염 문제까지 해결된 것은 아니다.

## 3. `07`/`08`: flow2 후보국 집계가 raw row 평균임

### 위치

- `notebooks/07_flow0_flow2_analysis.ipynb`: flow2 분석 셀
- `notebooks/08_comtrade_flow1_collection.ipynb`: 중간국 후보 선정 셀

현재 방식은 대체로 다음 구조다.

```python
groupby([... "country_iso2", "period_label"])
.agg(avg_imp_dlr=("imp_dlr", "mean"))
```

### 확인 결과

flow2 현재값은 정상적인 월평균보다 작게 계산되는 경향이 있다.

- before 기준 현재 raw-row 평균 / 정상 월평균 평균: 약 0.75
- after 기준 현재 raw-row 평균 / 정상 월평균 평균: 약 0.77

대표 예시:

| source_row_id | 국가 | 현재 after raw-row 평균 | 월별 합산 후 평균 |    차이 |
| ------------: | ---- | ----------------------: | ----------------: | ------: |
|            60 | JP   |                   7.39M |            45.59M | -38.19M |
|            32 | ID   |                   4.96M |            26.47M | -21.51M |
|            31 | ID   |                   4.96M |            26.47M | -21.51M |
|            30 | ID   |                   4.96M |            26.47M | -21.51M |
|            57 | CN   |                   1.53M |            18.30M | -16.78M |

다만 현재 데이터에서 flow2 top5 후보국 구성은 월평균 방식으로 바꿔도 바뀌지 않았다. 즉 후보국 순위는 유지되었지만 금액과 증가율은 왜곡된다.

### 상세 사유

관세청 API는 HS 6단위 질의에 대해 더 세분화된 HS 코드 row를 반환할 수 있다. 이때 같은 월, 같은 국가에 여러 row가 존재한다.

분석 단위가 "중간국 -> 한국의 월별 수입액"이라면 같은 월과 같은 국가의 모든 HS row를 먼저 합산해야 한다. 현재처럼 row 평균을 내면 하위품목 row가 많은 국가일수록 금액이 희석된다.

### 영향

- flow2 증가액과 증가율이 과소평가될 수 있다.
- `07`의 우회 의심 점수와 후보국별 수치가 왜곡된다.
- `08`에서 flow1 수집 대상 후보국의 금액 기준 해석이 부정확해진다.

### 보완 방향

flow2는 다음 순서로 집계해야 한다.

1. `source_row_id, country_iso2, trade_date, period_label` 기준으로 `imp_dlr`를 합산한다.
2. 그 월별 합계를 before/after별로 평균한다.
3. 후보국 선정은 after 금액만이 아니라 증가액, 증가율, 최소 거래금액을 함께 고려한다.

### 최신 상태

`07_flow0_flow2_analysis.ipynb`와 `08_comtrade_flow1_collection.ipynb` 모두 flow2 집계를 월별 합산 후 월평균 방식으로 수정했다. raw row 평균 문제는 해결된 것으로 판단한다.

다만 `08`은 후보국 선정 입력을 만들 때 여전히 다음과 같이 기존 `flow == 2`를 사용한다.

```python
df_f2 = df_flow2_all[df_flow2_all["flow"] == 2].copy()
```

따라서 집계 방식은 맞지만, 후보군 자체가 corrected flow2 기준이 아니다.

## 4. `09`: 최종 삼각무역 분석이 총합 기준이라 의심 케이스가 바뀜

### 위치

`notebooks/09_triangular_trade_analysis.ipynb`의 `before_after_pivot()` 함수.

현재 함수는 다음 구조다.

```python
df.groupby(group_cols + ["period_label"])[value_col].sum()
```

즉 before/after 기간 총합을 비교한다.

### 확인 결과

before/after 월 수는 균등하지 않다.

| after 월수 | before 월수 | 사건 수 |
| ---------: | ----------: | ------: |
|         12 |          12 |      37 |
|         12 |          11 |      14 |
|         11 |          12 |       3 |
|          5 |          11 |       2 |
|          9 |          12 |       1 |
|          8 |          12 |       1 |
|          7 |          12 |       1 |
|          6 |          11 |       1 |

총합 기준과 월평균 기준의 최종 의심 케이스를 비교하면 다음과 같다.

| 기준           | 의심 조합 수 | 의심 source_row_id 수 |
| -------------- | -----------: | --------------------: |
| 현재 총합 기준 |           37 |                    25 |
| 월평균 기준    |           31 |                    22 |

차이:

- 총합 기준에서만 의심으로 잡힌 조합: 9개
- 월평균 기준에서만 의심으로 잡힌 조합: 3개

### 상세 사유

최종 판별식은 다음 세 조건을 동시에 요구한다.

```python
(f0_pct < 0) & (f2_pct > 0) & (f1_pct > 0)
```

총합 기준에서는 월 수가 많은 기간이 유리하다. 예를 들어 after가 12개월, before가 11개월이면 실제 월평균이 거의 같아도 after 총합이 더 커져 증가로 판정될 수 있다. 반대로 after 관측치가 적은 최근 사건은 실제 월평균이 증가해도 총합은 감소처럼 보일 수 있다.

### 영향

이 문제는 단순 표시 오류가 아니라 최종 `is_suspect` 값과 `suspicion_score`를 직접 바꾼다. 따라서 `circumvention_suspects.csv`를 해석하기 전에 반드시 집계 기준을 정정해야 한다.

### 보완 방향

`before_after_pivot()`을 월별 합계 후 월평균 방식으로 바꾸는 것이 우선이다.

권장 구조:

1. `group_cols + ["period", "period_label"]` 기준으로 월별 합계를 만든다.
2. `group_cols + ["period_label"]` 기준으로 월평균을 계산한다.
3. before/after를 pivot한다.
4. 관측 월 수를 함께 저장해 최소 관측 개월 수 필터를 둔다.

### 최신 상태

`09_triangular_trade_analysis.ipynb`의 `before_after_pivot()`은 월별 합산 후 월평균 방식으로 수정되었다. 최신 실행 출력 기준 (v4, trade_date 수정 후 재실행):

- flow0 집계: 60행
- flow2 집계: 3,652행
- flow1 집계: 589행
- 최종 조합: 3,652건
- 우회 의심 조합: **43건** (v3 동일)
- 우회 의심 source_row_id: **23개** (v3: 25개, trade_date 수정으로 2개 탈락)
- 1위: 스테인리스평판압연/VN (suspicion_score 6,382.1, v3: 4,213.5)

월 수 불균형에 따른 총합 비교 문제는 해결된 것으로 판단한다.

## 5. `08`: TWN flow1 누락

### 위치

`notebooks/08_comtrade_flow1_collection.ipynb`의 Comtrade reporter 코드 매핑 및 `missing_codes` 처리.

### 확인 결과

원자화 데이터에는 대만(`TWN`) 관련 규제 사건이 존재한다.

- TWN 관련 `source_row_id`: 16, 22, 36, 37, 56, 58
- `comtrade_flow1_raw.csv`의 `origin_country_iso3 == "TWN"` 행 수: 0
- flow1 결과의 origin 목록에도 `TWN` 없음

### 상세 사유

Comtrade에서 대만은 일반 ISO3 `TWN` 그대로 매핑되지 않고 `Other Asia, nes` 등 별도 reporter 코드로 관리되는 경우가 있다. 자동 reference 매핑만 사용하면 `TWN` reporter code가 결측이 되어 수집 대상에서 제외된다.

### 영향

대만이 규제국인 사건은 flow1이 누락된다. 그 결과 `f1_pct > 0` 조건을 통과하지 못하거나, 대만 외 다른 규제국만으로 flow1이 계산되어 교차검증이 불완전해진다.

### 보완 방향

Comtrade reporter reference에서 대만에 해당하는 코드를 명시적으로 확인하고 수동 매핑을 추가해야 한다. 매핑 후 TWN 관련 source row의 flow1을 재수집해야 한다.

### 최신 상태

`08_comtrade_flow1_collection.ipynb`에 다음 수동 매핑이 추가되었다.

```python
iso3_to_reporter["TWN"] = "490"
```

최신 산출물 기준:

- `comtrade_flow1_raw.csv`: 18,375행
- TWN flow1 행: 1,000행
- TWN 관련 source_row_id: 16, 22, 36, 37, 56, 58
- Comtrade 코드 매핑 실패: 0건

TWN 누락 문제는 해결된 것으로 판단한다. 다만 `490`은 `Other Asia, nes` 성격의 코드이므로, 해석 시 대만 단독 통계가 아닐 수 있다는 주석을 유지해야 한다.

## 5.1 최신 잔여 이슈: `08` flow1 후보 선정이 old flow 기준

### 위치

`notebooks/08_comtrade_flow1_collection.ipynb`의 입력 데이터 로드 직후:

```python
df_f2 = df_flow2_all[df_flow2_all["flow"] == 2].copy()
```

### 확인 결과

`09`에서는 `flow_corrected`를 사용하지만, `08`의 flow1 수집 후보는 여전히 기존 `flow` 기준이다. 최신 산출물을 재검산한 결과:

- 기존 `flow0`에서 corrected `flow2`로 바뀐 `(source_row_id, intermediary)` 조합: 22개
- 그 22개 중 flow1 행이 없는 조합: 22개

누락 조합은 다음과 같다.

| source_row_id | intermediary_iso2 | 국가명     |
| ------------: | ----------------- | ---------- |
|             5 | IN                | 인도       |
|             6 | CN                | 중국       |
|             6 | JP                | 일본       |
|             6 | SG                | 싱가포르   |
|            11 | CN                | 중국       |
|            12 | MY                | 말레이시아 |
|            23 | IN                | 인도       |
|            24 | CN                | 중국       |
|            24 | JP                | 일본       |
|            24 | SG                | 싱가포르   |
|            30 | CN                | 중국       |
|            30 | VN                | 베트남     |
|            31 | MY                | 말레이시아 |
|            31 | VN                | 베트남     |
|            32 | CN                | 중국       |
|            32 | MY                | 말레이시아 |
|            50 | MY                | 말레이시아 |
|            50 | VN                | 베트남     |
|            52 | CN                | 중국       |
|            52 | VN                | 베트남     |
|            53 | CN                | 중국       |
|            53 | MY                | 말레이시아 |

### 상세 사유

기존 `flow`에서는 이 국가들이 같은 HS/window 묶음의 규제국 합집합에 포함되어 flow0으로 분류되었다. 하지만 source-level 규제국 기준으로 재분류하면 해당 사건의 규제국이 아니므로 corrected flow2가 된다.

`09`는 corrected flow2로 이 국가들을 분석 대상에 포함한다. 그러나 `08`은 old flow2만 대상으로 flow1을 수집했기 때문에, 위 조합의 flow1 자료가 없다. 이후 `09`의 left join에서 `f1_before`, `f1_after`가 0으로 채워져 `f1_pct > 0` 조건을 통과하지 못할 수 있다.

### 영향

이 문제는 false positive보다는 false negative 위험이다. 즉 실제로 flow1 증가가 있었더라도 자료가 수집되지 않아 우회 의심 케이스에서 빠질 수 있다.

### 보완 방향

`08`에도 `09`와 동일한 source-level flow 재분류 로직을 넣고, 후보 선정은 `flow_corrected == 2` 기준으로 수행해야 한다. 이후 `comtrade_flow1_raw.csv`와 `circumvention_suspects.csv`를 다시 생성해야 한다.

## 5.2 ~~잔여 이슈~~ (해결): `10` 세계 평균 단가 수집 — 방향 전환 완료

### 원래 문제

`reporter=0, partner=0` (World → World) Comtrade API 요청이 유효한 데이터를 반환하지 않는다. 수집한 90개 캐시 파일의 `world_exp_dlr`, `world_net_wgt` 전부 0, `world_unit_price` 전부 NaN이었다.

### 해결 방향

세계 단가 수집 방식을 포기하고, **기존 관세청 데이터(`customs_flow0_flow2_raw.csv`)에서 직접 단가를 계산**하는 방식으로 노트북 10의 목적을 전환했다.

새 목적: 우회 의심 케이스(is_suspect=True)의 수입 금액 증가가 물량 때문인지 가격 상승 때문인지 분해

### 최신 상태

- 구 `10_comtrade_world_price_collection.ipynb` 삭제 완료
- 신규 `10_price_volume_decomposition.ipynb` 생성 및 실행 완료
- 산출물: `data/interim/price_volume_decomposition.csv` (43건)

신규 노트북 10의 분석 방법:
- `circumvention_suspects.csv`의 `is_suspect=True` 43개 조합을 `customs_flow0_flow2_raw.csv`에 조인
- (source_row_id, country_iso2) 기준 월별 합산 후 단가 = `imp_dlr / imp_wgt`
- before/after 기간 금액·중량·단가 변화 계산
- 유형 분류: 물량증가형 / 혼합형 / 가격상승형 / 신규유입형 / 기타 / 판정보류 / 해당없음

결과 요약 (43건, trade_date 수정 후 v4 기준):

| 유형 | 건수 |
|------|------|
| 물량증가형 | 27 |
| 신규유입형 | 5 |
| 혼합형 | 4 |
| 기타 | 4 |
| 가격상승형 | 2 |
| 판정보류(중량결측) | 1 |

물량증가형 27건(63%)으로 가격 상승만으로 설명되지 않는 금액 증가 후보가 다수 확인되었다. 다만 이는 우회 확정이나 통계적 유의성의 근거가 아니라, 추가 검토 우선순위를 정하는 보조 지표로 해석해야 한다. `f2_pct ≈ dlr_pct` 43/43 정합 확인 완료.

세계 단가 수집 문제 자체는 방향 전환으로 해결된 것으로 판단한다. 가격·물량 분해 산출값의 신뢰성은 Issue 5.4 수정 후 재검증해야 한다.

## 5.3 (해결): `09` hs_code dedup 누락 — flow2 금액 과소계산

### 위치

`notebooks/09_triangular_trade_analysis.ipynb` 전처리 셀의 중복 제거 로직:

```python
# 수정 전
dedup_keys = ["source_row_id", "trade_date", "country_iso2", "hs_code_query", "window_start", "window_end"]
df_f02_dedup = df_f02.drop_duplicates(subset=dedup_keys)
```

### 문제

관세청 API는 HS 6자리 쿼리에 대해 더 세분화된 10자리 코드 row를 반환한다. 예: `441239` 쿼리 → `4412391090`, `4412399010`, `4412399090` 등 여러 row.

기존 dedup 키에 `hs_code`(실제 10자리)가 없었기 때문에, 같은 (source_row_id, trade_date, country_iso2, hs_code_query) 조합에서 첫 번째 row만 남고 나머지 세부코드 row가 모두 버려졌다.

`before_after_pivot()`의 1단계 월별 합산은 올바르게 설계되어 있었지만, 입력 데이터가 이미 세부코드별로 잘려 있어 합산 효과가 없었다.

### 영향

- flow2 before/after 금액이 실제보다 과소계산됨
- 세부코드가 많은 품목(합판, 스테인리스 등)일수록 underestimation 심각
- `f2_pct` 값이 실제보다 작거나 크게 왜곡될 수 있음

대표 예시 (수정 전 vs 수정 후 비교):

| source_row_id | 국가 | 수정 전 f2_pct | 수정 후 f2_pct |
|--------------|------|--------------|--------------|
| 36 (스테인리스평판압연) | VN | 누락 (is_suspect 미포함) | +4,131% (1위) |
| 38 (폴리에스테르장섬유) | VN | 누락 | +1,234% (4위) |
| 8 (침엽수합판) | VN | +263% | +10% (재산정) |

### 해결

```python
# 수정 후
dedup_keys = [
    "source_row_id", "trade_date", "country_iso2",
    "hs_code_query", "window_start", "window_end", "hs_code",
]
```

시각화 함수(`plot_triangle_case`) 내부 dedup도 동일하게 수정.

### 최신 상태

수정 후 버전 이력:

| 버전 | 의심 조합 | 의심 사건 | 변경 사유 |
|------|----------|-----------|----------|
| v1 (총합 기준) | 37건 | — | 최초 |
| v2 (월평균) | 34건 | 23개 | Issue 3·4 수정 |
| v3 (hs_code dedup) | **43건** | **25개** | Issue 5.3 수정 |
| v4 (trade_date 수정) | **43건** | **23개** | Issue 5.4 수정 (2개 사건 탈락, 점수 변동) |

v4 기준 1위: 스테인리스평판압연/VN (suspicion_score 6,382.1)

해결된 것으로 판단한다.

## 5.4 ~~잔여 이슈~~ (해결): customs `trade_date` float 저장으로 월 정보 손실

### 위치

- `notebooks/06_customs_flow0_flow2_collection.ipynb`
  - 기존 `customs_flow0_flow2_raw.csv` 기반 cache seeding
  - `data/interim/cache/customs/*.parquet`
  - `data/interim/customs_flow0_flow2_raw.csv`
- `notebooks/07_flow0_flow2_analysis.ipynb`
  - `pd.read_csv(INPUT_PATH)`
  - `pd.to_datetime(df["trade_date"].astype(str), format="%Y.%m")`
- `notebooks/09_triangular_trade_analysis.ipynb`
  - `pd.read_csv(F02_PATH)`
  - `pd.to_datetime(df_f02["trade_date"].astype(str), format="%Y.%m")`
- `notebooks/10_price_volume_decomposition.ipynb`
  - `pd.read_csv(CUSTOMS_PATH)`
  - `pd.to_datetime(customs["trade_date"].astype(str), format="%Y.%m")`

### 확인 결과

`data/interim/customs_flow0_flow2_raw.csv`의 `trade_date`는 CSV와 parquet cache 모두 float 형태로 저장되어 있다.

예시:

```text
trade_date dtype: float64
2020.10 count: 0
2020.1 count: 1,183
pd.to_datetime("2020.1", format="%Y.%m") -> 2020-01
```

즉 `YYYY.10`이어야 할 10월 값이 `YYYY.1`로 저장되어, 이후 파싱 단계에서 1월로 해석된다. 같은 문제가 `2014.10`, `2021.10`, `2025.10` 등 모든 10월에 발생할 수 있다.

또한 `data/interim/cache/customs/*.parquet`를 직접 확인한 결과 cache 내부의 `trade_date`도 `float64`다. 따라서 CSV만 dtype 지정해서 다시 읽는 방식으로는 이미 손실된 10월 정보를 복구할 수 없다.

### 상세 사유

관세청 API의 월 정보는 원래 `YYYYMM`이며, 06번 노트북의 최신 파서에는 `YYYY-MM` 문자열로 변환하는 코드가 있다.

```python
raw_date = item.findtext("year", "")
trade_date = f"{raw_date[:4]}-{raw_date[4:]}" if len(raw_date) == 6 else raw_date
```

하지만 현재 산출물과 cache에는 `2016.05`, `2020.1` 같은 float형 표현이 남아 있다. 이는 과거 실행 결과를 CSV에서 다시 읽거나 cache seeding하는 과정에서 `trade_date`가 숫자로 추론되면서 월의 leading zero와 10월의 두 자리 표현이 손실된 것으로 보인다.

`2020.10`과 `2020.1`은 문자열로는 구분되어야 하지만, float로 저장되면 둘 다 `2020.1`이 된다. 이 손실은 사후 파싱으로 복구할 수 없다.

### 영향

이 문제는 10번 산출값만의 문제가 아니라, 07/09/10의 before/after 라벨과 월평균 계산을 모두 흔든다.

- 10월 자료가 1월로 이동해 `period_label`이 잘못 붙을 수 있다.
- 규제 시작월 근처 사건에서 before/after 판정이 달라질 수 있다.
- 월별 합산 후 월평균의 분모(`n_months`)와 월별 금액이 왜곡될 수 있다.
- 09의 `f2_before`, `f2_after`, `f2_pct`와 10의 `avg_dlr_before`, `avg_dlr_after`, `dlr_pct`가 서로 맞지 않는 원인이 될 수 있다.

실제 비교 결과, `circumvention_suspects.csv`의 43개 의심 조합은 `price_volume_decomposition.csv`에 모두 포함되지만, 09의 `f2_pct`와 10의 `dlr_pct`는 43건 중 33건에서 차이가 났다. 최대 차이는 약 2,639.5%p였다.

대표 예시:

| source_row_id | 품목 | 국가 | 09 f2_pct | 10 dlr_pct |
|--------------:|------|------|----------:|-----------:|
| 36 | 스테인리스평판압연 | VN | 4,130.7% | 6,770.2% |
| 45 | 수산화알루미늄 | IN | 129.6% | 448.9% |
| 38 | 폴리에스테르 장섬유 완전연신사 | VN | 1,234.3% | 1,483.7% |

10번은 09의 의심 flow2 금액 증가를 가격·물량으로 분해하는 보조 분석이다. 따라서 같은 조합의 금액 before/after 및 증감률은 원칙적으로 09의 flow2 값과 일치해야 한다.

### 보완 방향

1. `06`에서 customs API raw 결과의 `trade_date`를 `YYYY-MM` 문자열로 고정한다.
2. 기존 `data/interim/customs_flow0_flow2_raw.csv`와 `data/interim/cache/customs/*.parquet`는 재생성한다.
   - 이미 float로 저장된 cache는 10월 정보를 복구할 수 없으므로 그대로 재사용하면 안 된다.
   - API 재호출이 부담이면 원 API 응답 원본이 남아 있는지 먼저 확인하고, 없으면 06 재수집이 필요하다.
3. `07`, `09`, `10`의 파싱은 `%Y-%m` 기준으로 통일한다.
4. `09`와 `10`은 같은 dedup key와 같은 월 기준을 사용하도록 맞춘다.
5. 수정 후 다음 검증을 통과해야 한다.
   - `customs_flow0_flow2_raw.csv`에서 `trade_date` dtype이 문자열
   - `YYYY.1` 형태가 없음
   - `YYYY-10` 형태가 정상 존재
   - 43개 의심 조합에서 `09 f2_before/after/pct`와 `10 avg_dlr_before/after/dlr_pct`가 허용 오차 내 일치

### 해결 내용

**수행 단계:**

1. 84개 parquet cache 파일의 `trade_date`(float64)를 `YYYY-MM` 문자열로 일괄 변환 (`2020.1` → `"2020-10"` 등, float 산술 역산으로 정확히 복원 가능)
2. `customs_flow0_flow2_raw.csv` 재생성 (141,907행, 10월 11,354행 복원)
3. notebooks 07/09/10의 파싱 코드를 `format="%Y.%m"` → `format="%Y-%m"`으로 수정
4. notebook 09 재실행 → `circumvention_suspects.csv` 재생성 (43건 / 23개 사건)
5. notebook 10 재실행 → `price_volume_decomposition.csv` 재생성

**검증 결과:**

- `trade_date` dtype: object (문자열 `YYYY-MM`)
- `YYYY.1` 형태: 0건
- `YYYY-10` (10월) 형태: 11,354건
- `09 f2_pct` vs `10 dlr_pct`: 43/43건 허용오차(1%) 내 일치

**영향 (trade_date 수정 전후 비교):**

| 항목 | 수정 전 (v3) | 수정 후 (v4) |
|------|------------|------------|
| 의심 조합 수 | 43건 | 43건 (동일) |
| 의심 사건 수 | 25개 | 23개 (2개 탈락) |
| 1위 suspicion_score | 4,213.5 | 6,382.1 |
| f2_pct / dlr_pct 정합 | 33/43 | 43/43 |

해결된 것으로 판단한다.

## 6. 이론 및 방법론상 보완 사항

### 6.1 후보국 선정 편향

`08`은 flow2의 after 금액이 큰 국가를 먼저 후보국으로 고르고, 이후 다시 flow2 증가를 우회 신호로 사용한다. 순수 통계 검정이라면 선택 편향이지만, 이 분석의 목적이 의심 케이스 탐색이라면 치명적 결함보다는 해석상 주의사항으로 보는 것이 적절하다.

보완 방향:

- 후보국 선정 기준과 최종 판정 기준을 분리한다.
- after 금액만이 아니라 증가액, 증가율, 최소 거래금액을 함께 사용한다.
- 가능하면 모든 flow2 국가를 대상으로 점수를 계산한 뒤 사후적으로 상위 케이스를 해석한다.

### 6.2 자료원 차이

flow0/flow2는 한국 관세청 수입자료이고 flow1은 UN Comtrade 수출자료다. 두 자료는 신고 기준, 가격 기준, 집계 시점이 다를 수 있다.

- 한국 수입자료는 CIF 성격일 수 있다.
- Comtrade 수출자료는 FOB 성격일 수 있다.
- 재수출, 통관 시점 차이, mirror discrepancy가 존재할 수 있다.

before/after 방향성 비교에서는 이 차이가 완전히 치명적이지는 않다. 다만 세 흐름의 금액 레벨을 같은 척도처럼 직접 비교하기보다 방향성과 동시성 검증 중심으로 해석해야 한다.

### 6.3 `before=0` 증가율 처리

현재 `pct_change()`는 before가 0이고 after가 양수이면 100%로 클리핑한다. 이 방식은 신규 거래의 크기를 충분히 반영하지 못하고, 작은 before 값의 폭증 문제도 안정적으로 처리하지 못한다.

보완 방향:

- `log1p(after) - log1p(before)` 사용
- 최소 before/after 금액 하한 적용
- 증가율과 절대 증가액을 동시에 점수화

### 6.4 HS 코드 이력

06-09 흐름에는 HS 코드 개정 또는 세분화 이력 매핑이 통합되어 있지 않다. 장기 재심 사건에서는 같은 상품이 기간 중 다른 HS 코드로 이동했을 수 있다.

보완 방향:

- HS 코드 이력 매핑 결과를 flow0/flow1/flow2 수집 전 단계에 반영한다.
- 기간 중 코드 변경이 있는 품목은 old/new 코드 세트를 함께 조회한다.

### 6.5 API 키 출력

초기 검토 당시 `08`에 `API_KEY[:8]` 출력이 남아 있었다. 최신 재리뷰에서는 `API_KEY[:8]`, `새 키 적용`, 키 앞자리 출력 문자열이 검색되지 않았다. 이 문제는 해결된 것으로 판단한다.

### 6.6 대조군 부재와 통계적 유의성 미검증

현재 43개 의심 조합은 전체 3,652개 `(source_row_id × intermediary)` 조합 중 약 1.2%다. 그러나 이 비율이 높은지 낮은지는 현재 설계만으로 판단할 수 없다.

핵심 이유는 대조군이 없기 때문이다. 반덤핑 규제와 무관한 유사 품목·유사 국가 조합에서도 `f0 감소 + f1 증가 + f2 증가` 패턴이 우연히 비슷한 빈도로 발생한다면, 현재 의심 조합 수는 규제 효과의 특이 신호라고 보기 어렵다.

따라서 현재 결과는 다음 수준으로 해석해야 한다.

- 가능: "반덤핑 규제 이후 우회무역과 일관된 방향의 1-hop 삼각무역 패턴 후보를 식별했다."
- 불가: "통계적으로 유의미한 우회무역을 검증했다."
- 불가: "반덤핑 규제로 인해 우회무역이 발생했다."

통계적 유의성을 주장하려면 최소한 다음 보완이 필요하다.

- 규제 대상 품목과 유사하지만 규제되지 않은 HS 품목을 대조군으로 구성
- 규제 전후 기간을 동일하게 잡아 처리군/대조군의 변화율 비교
- 품목 고정효과, 중간국 고정효과, 시점 고정효과 등을 포함한 DiD 또는 event-study 구조 검토

### 6.7 글로벌 공급망 재편과의 구분 한계

상위 의심 케이스 중 중국 규제국 + 베트남 중간국 조합은 특히 조심해서 해석해야 한다. 2020년대 이후 중국에서 베트남으로의 생산기지 이전, 차이나+1 전략, 글로벌 공급망 재편은 반덤핑 우회와 무관하게 진행된 구조적 현상이다.

현재 1-hop 지표는 다음 두 현상을 관측상 구분하기 어렵다.

- 우회 가능성: 중국산 물품이 베트남을 경유해 한국으로 들어옴
- 정상 공급망 재편: 생산 또는 조달 자체가 중국에서 베트남으로 이전됨

두 경우 모두 데이터상으로는 `중국 -> 한국 직접수입 감소`, `중국 -> 베트남 수출 증가`, `베트남 -> 한국 수입 증가`로 나타날 수 있다. 따라서 중국 -> 베트남 케이스는 우회 의심 후보로 남기되, 보고서 본문에서는 "공급망 재편이라는 대안 설명을 배제하지 못한다"고 명시해야 한다.

구분력을 높이려면 다음 자료 또는 분석이 추가로 필요하다.

- 원산지, 재수출, 환적 또는 보세구역 관련 자료
- 중간국의 해당 품목 생산능력 또는 수출단가 변화
- 규제 없는 유사 품목 대비 중간국 수입 증가폭 비교
- 기업 단위 거래자료 또는 품목별 부가가치 정보

### 6.8 권장 결론 문구

현재 보고서의 결론은 다음처럼 제한적으로 쓰는 것이 안전하다.

> 본 분석은 반덤핑 조치 이후 규제국 직접수입 감소, 규제국의 중간국향 수출 증가, 중간국의 대한국 수출 증가가 동시에 관측되는 1-hop 삼각무역 패턴을 탐색했다. 이는 우회무역의 확정 증거가 아니라, 추가 검토가 필요한 고위험 후보군을 식별하기 위한 조기경보 지표로 해석한다.

피해야 할 표현:

- "우회무역이 발생했다"
- "통계적으로 유의미한 우회 사례를 검증했다"
- "반덤핑 규제의 인과 효과를 확인했다"

## 수정 우선순위

### 완료된 항목

| 항목 | 내용 |
|------|------|
| `09` flow 재분류 | `flow_corrected` 도입 완료 |
| `07`/`08` flow2 집계 | 월별 합산 후 월평균 방식으로 수정 완료 |
| `07` flow0 집계 | trade_date 포함 월별 집계 후 평균 수정 완료 |
| `08` TWN 매핑 | `TWN → 490` 수동 매핑, flow1 1,000행 수집 완료 |
| `09` hs_code dedup | `hs_code` 추가 → 세부코드 보존, 43건/23개 사건 재산정 완료 (trade_date 수정 후) |
| `10` 방향 전환 | World→World 단가 수집 포기, 가격·물량 분해 노트북으로 대체 완료 |
| `10` 신규유입형 분류 | before 기저 없는 케이스를 별도 유형으로 분리 완료 |
| customs `trade_date` | cache float 변환 + CSV 재생성 + 07/09/10 파싱 수정 + 재실행 완료 |

### 남은 항목 (우선순위순)

1. **(medium)** `08`에서 `flow_corrected == 2` 기준으로 flow1 후보국을 재선정한다.
   - 영향: 22개 조합 flow1 누락 → false negative 가능성
   - 현재 상위 의심 케이스에는 미포함 → 즉각 critical하지 않음
   - 수행 시 `comtrade_flow1_raw.csv` → `circumvention_suspects.csv` → `price_volume_decomposition.csv` 순 재실행 필요

2. **(low)** `07` 탐색 분석에 old `flow` 기준임을 노트북 상단에 명시한다.
   - `flow_corrected` 기준으로 업데이트하거나, "보정 전 탐색용" 주석 추가

3. **(low)** 최종 의심 케이스 버전별 이력을 Issue 5.3 섹션 표에서 확인한다.
   - v1 (총합): 37건 / v2 (월평균): 34건/23개 / v3 (hs_code dedup): 43건/25개 / v4 (trade_date): 43건/23개
