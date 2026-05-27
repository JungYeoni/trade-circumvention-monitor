# 노트북별 점검 요약

## `01_un_comtrade_api_example.ipynb`

### 역할

UN Comtrade API 사용법을 확인하는 기초 노트북이다. 베트남의 한국 대상 철강 수출 데이터를 예시로 연간 데이터를 조회한다.

### 확인 내용

- `comtradeapicall.getFinalData()` 사용법 확인
- 연간 데이터 조회 파라미터 정리
- Comtrade 응답 컬럼 의미 정리
- `primaryValue`를 분석용 주요 금액으로 사용할 수 있음을 확인

### 실행 결과

베트남의 한국 대상 HS 72 철강 수출액 예시가 2020-2023년 4개 연도에 대해 조회되었다.

| 연도 | 수출액 USD |
|---:|---:|
| 2020 | 176,431,200 |
| 2021 | 356,653,803 |
| 2022 | 580,456,200 |
| 2023 | 464,059,500 |

### 보완 사항

- 2024년을 요청했지만 출력에는 2020-2023년만 확인된다. 2024년 데이터 누락 원인을 확인해야 한다.
- 예시 노트북이므로 프로젝트 핵심 분석과 직접 연결되는 설명을 추가하면 좋다.

## `02_customs_trade_api_example.ipynb`

### 역할

관세청 품목별 국가별 수출입실적 API 연동과 월별 데이터 수집 함수를 검증하는 노트북이다.

### 확인 내용

- API 요청/응답 파라미터 정리
- XML 응답 파싱
- 총계 행 제외
- 금액·중량 컬럼 정수 변환
- 1년 초과 기간 자동 분할 함수 작성

### 실행 결과

HS `1001999090`, 국가 `US` 기준 예시 조회가 정상서비스 코드로 실행되었다.

- 2015.02-2016.01 예시: 미국 대상 수입액과 수출액 월별 출력
- 2024.05-2026.02 예시: 기간 자동 분할 후 월별 출력
- 대부분 월에서 수출액은 0이고 수입액이 중심인 품목으로 확인됨

### 보완 사항

- 함수가 노트북에만 있으므로 재사용하려면 `src/data` 모듈로 이동하는 것이 좋다.
- 분석 목적에 맞게 관세청 데이터가 어떤 검증 또는 보조 분석에 쓰이는지 연결 설명이 필요하다.

## `03_russia_sanctions_trade_shift_analysis.ipynb`

### 역할

프로젝트 핵심 분석 노트북이다. 제재 전후 특정 제3국의 대러 수출 증가 여부를 월별 데이터로 비교한다.

### 확인 내용

- `collect_russia_trade()`로 2020-2024년 월별 대러 수출입 데이터 수집
- HS 7210, HS 8542 필터링
- 월별 시계열 생성
- 2022년 2월 기준 제재 전후 평균 비교
- 증가율과 절대 증가액 산출
- 국가 유형 분류
- 결측 개월 수 확인

### 핵심 산출

- HS 8542: 아르메니아와 카자흐스탄이 제재 후 핵심 증가국
- HS 7210: 카자흐스탄은 기존 중심국, 튀르키예는 제재 후 부상국
- UAE는 전 기간 미수집으로 제외 필요
- 조지아는 결측 과다로 보조 사례 처리 필요

### 보완 사항

- 노트북에서 `all_df.to_csv("comtrade_monthly_2020_2024_russia_7210_8542.csv")`를 호출하지만 현재 저장 파일은 확인되지 않는다.
- 수집 데이터는 `data/raw` 또는 `data/interim` 아래에 저장하도록 경로를 고정하는 것이 좋다.
- 평균 기반 비교 외에 중앙값, 합계, 관측 개월 수 보정 지표를 추가하면 해석 안정성이 높아진다.
- 시각화 결과를 `reports` 또는 `reports/figures`에 저장하면 보고서 재현성이 좋아진다.

---

## `05_regulation_events_atomize.ipynb`

### 역할

반덤핑 규제 이벤트 테이블을 분석에 사용할 수 있도록 원자화(atomize)하는 노트북이다. 2015년 이전 시작 사건만 필터링하고, 수집 기간(window_start/end)과 활성 여부를 추가한다.

### 확인 내용

- `regulation_events.csv` 입력 (275행) → 2015년 이전 시작 사건 필터링
- `window_start`, `window_end` 컬럼 생성 (규제 시작 1년 전 ~ 규제 시작 1년 후)
- `is_active_as_of_extract` 플래그 추가
- `duration_days` 산출

### 핵심 산출

- 출력: `data/interim/regulation_events_atomic(~2015).csv`
- 행 수: 155행 / 고유 source_row_id: 62개
- 수집 기간: 2014-01 ~ 2026-12

### 보완 사항

- window 설정이 단순 ±1년 고정이라 규제 효과 지연을 반영하지 못할 수 있다.

---

## `06_customs_flow0_flow2_collection.ipynb`

### 역할

반덤핑 규제 이벤트별로 관세청 API를 호출해 규제국→한국(flow0)과 제3국→한국(flow2) 수입 데이터를 수집한다.

### 확인 내용

- `regulation_events_atomic(~2015).csv`에서 HS 코드·기간 추출
- 관세청 API 월별 호출 (캐싱: `data/interim/cache/customs/`)
- `flow` 컬럼 부여: 규제국이면 flow=0, 아니면 flow=2
- 규제 메타(source_row_id, product_name_kr, start_date 등) 병합

### 핵심 산출

- 출력: `data/interim/customs_flow0_flow2_raw.csv`
- 행 수: 141,907행 / 컬럼 수: 17
- 캐시: `data/interim/cache/customs/*.parquet` 84개

### 알려진 문제

- **[미해결 - critical]** `trade_date`가 float64로 저장되어 10월(`YYYY.10`)이 `YYYY.1`로 손실됨. 캐시도 동일하게 오염. 06 재수집 시 `YYYY-MM` 문자열로 고정 필요 (Issue 5.4 참조).
- `flow` 분류가 HS/window 묶음 단위 규제국 합집합 기준이라 사건 간 오분류 가능. `09`에서 `flow_corrected`로 보정.

---

## `07_flow0_flow2_analysis.ipynb`

### 역할

수집된 flow0/flow2 데이터를 탐색·시각화하는 노트북이다. 규제 전후 월평균 수입액을 비교하고 우회 후보국 상위 목록을 산출한다.

### 확인 내용

- flow0: source_row_id × trade_date 기준 월별 합산 후 before/after 월평균
- flow2: (source_row_id, country_iso2) × trade_date 기준 월별 합산 후 before/after 월평균
- 우회 후보국 top-N 시각화

### 핵심 산출

탐색용 분석. 별도 저장 파일 없음. 의심 케이스 최종 판단은 09에서 수행.

### 보완 사항

- 여전히 기존 `flow` 컬럼 기준 (flow_corrected 미적용). 탐색용으로만 사용.
- trade_date float 파싱 문제(Issue 5.4) 수정 후 재실행 필요.

---

## `08_comtrade_flow1_collection.ipynb`

### 역할

규제국→중간국 수출(flow1) 데이터를 UN Comtrade API로 수집한다. flow2 상위 후보국을 대상으로 규제국별 수출 증가 여부를 확인한다.

### 확인 내용

- flow2 top 후보국 선정 → Comtrade API 수출 데이터 수집
- ISO3 → Comtrade reporter 코드 매핑 (`comtradeapicall` reference 활용)
- TWN 수동 매핑 추가: `iso3_to_reporter["TWN"] = "490"`
- 캐싱: `data/interim/cache/comtrade_flow1/`

### 핵심 산출

- 출력: `data/interim/comtrade_flow1_raw.csv`
- 행 수: 18,375행 / 컬럼 수: 14
- 고유 중간국: 42개 / 고유 규제국: 19개

### 알려진 문제

- **[미해결 - medium]** 후보국 선정이 기존 `flow == 2` 기준. `flow_corrected == 2` 기준으로 변경 시 22개 조합 추가 수집 필요.
- `TWN` 매핑 코드 490은 `Other Asia, nes` 성격으로 대만 단독 통계가 아닐 수 있음.

---

## `09_triangular_trade_analysis.ipynb`

### 역할

flow0·flow1·flow2를 결합해 삼각무역 우회 의심 케이스를 탐지하고 `circumvention_suspects.csv`를 생성하는 핵심 분석 노트북이다.

### 확인 내용

- `flow_corrected` 재분류: source_row_id별 규제국 집합 기준 (기존 HS/window 묶음 오류 보정)
- `before_after_pivot()`: 월별 합산 후 월평균 방식 (총합 비교 오류 수정)
- dedup_keys에 `hs_code` 포함 (세부코드 row 보존)
- flow1 집계: (source_row_id, intermediary_iso2) 수준으로 합산
- 우회 조건: f0_pct < 0 & f2_pct > 0 & f1_pct > 0 동시 충족

### 핵심 산출

- 출력: `data/interim/circumvention_suspects.csv`
- 전체 조합: 3,652건 (source_row_id × intermediary_iso2)
- is_suspect=True: **43건** / 고유 사건: **23개**
- 1위: 스테인리스평판압연/VN (suspicion_score 6,382.1)

### 버전 이력

| 버전 | 의심 조합 | 고유 사건 | 변경 사유 |
|------|----------|----------|----------|
| v1 (총합 기준) | 37건 | — | 최초 |
| v2 (월평균) | 34건 | 23개 | Issue 3·4 수정 |
| v3 (hs_code dedup) | **43건** | 25개 | Issue 5.3 수정 |
| v4 (trade_date 수정) | **43건** | **23개** | Issue 5.4 수정 |

### 보완 사항

- flow1 후보국이 old flow 기준이라 22개 조합 flow1 누락 가능성 (medium 우선순위).

---

## `10_price_volume_decomposition.ipynb`

### 역할

우회 의심 케이스(is_suspect=True)의 수입 금액 증가가 물량 때문인지 단가 상승 때문인지 분해한다.

### 확인 내용

- `circumvention_suspects.csv`(is_suspect=True 43건)를 `customs_flow0_flow2_raw.csv`에 조인
- (source_row_id, country_iso2) 기준, flow 필터 없이 조인 (suspects가 이미 flow_corrected 기준)
- 월별 합산 후 단가 = `imp_dlr / imp_wgt`
- before/after 금액·중량·단가 변화율 계산
- 유형 분류: 물량증가형 / 혼합형 / 가격상승형 / 신규유입형 / 기타 / 판정보류 / 해당없음

### 핵심 산출

- 출력: `data/interim/price_volume_decomposition.csv`
- 43건 커버

| 유형 | 건수 |
|------|------|
| 물량증가형 | 27 |
| 신규유입형 | 5 |
| 혼합형 | 4 |
| 기타 | 4 |
| 가격상승형 | 2 |
| 판정보류(중량결측) | 1 |

물량증가형 27건(63%)이 다수 — 가격 효과가 아닌 물량 증가로 우회 신호의 질이 높음.

### 보완 사항

- 09의 `f2_pct`와 10의 `dlr_pct` 43/43건 정합 확인 완료 (trade_date 수정 후).
