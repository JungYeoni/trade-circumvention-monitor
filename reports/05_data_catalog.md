# 데이터 카탈로그

## 개요

이 문서는 프로젝트에서 사용하는 모든 데이터 파일의 구조, 출처, 컬럼 정의를 정리한다.

| 경로 | 용도 |
|------|------|
| `data/raw/` | 원천 데이터 (수정 금지) |
| `data/interim/` | 수집·전처리 중간 산출물 |
| `data/processed/` | 분석·모델링용 최종 데이터 |

> `data/interim/`, `data/processed/`는 `.gitignore` 대상이다. 파일은 로컬 또는 외부 저장소(Google Drive 등)에서 관리한다.

---

## data/raw

### 산업통상부\_무역구제 덤핑방지 관세 부과 현황\_20251231.csv

| 항목 | 내용 |
|------|------|
| 출처 | 산업통상부 공공데이터포털 |
| 형식 | CSV |
| 인코딩 | CP949 |
| 행 수 | 160 |
| 컬럼 수 | 6 |
| 기준일 | 2025-12-31 |
| 성격 | 한국 반덤핑 관세 부과 이력 원천 데이터 |

#### 컬럼 정의

| 컬럼 | 타입 | 결측 | 고유값 | 설명 |
|------|------|-----:|------:|------|
| `국가명` | str | 0 | 53 | 부과 대상 국가 (복수 국가는 쉼표 구분) |
| `품목` | str | 0 | 120 | 반덤핑 관세 부과 품목명 |
| `관세부과범위` | str | 0 | 138 | 관세율·가격약속·기준가격 차액 등 혼재 |
| `부과시작일` | str | 0 | 129 | 관세 부과 시작일 |
| `부과종료일` | str | 0 | 127 | 관세 부과 종료일 |
| `관련법령` | str | 0 | 156 | 고시·공고·대통령령 등 법령 근거 |

#### 사용상 주의

- `국가명`에 `일본,대만`처럼 복수 국가가 하나의 셀에 들어간 값이 있다. 전처리 시 행 분리 필요.
- `관세부과범위`는 숫자 관세율과 `가격약속` 등 텍스트가 혼재한다.
- 날짜 컬럼은 문자열로 저장돼 있다. 분석 시 `datetime64`로 변환 필요.

---

## data/interim

### regulation_events.csv

| 항목 | 내용 |
|------|------|
| 생성 노트북 | `notebooks/04_regulation_event_preprocessing.ipynb` |
| 원천 | `data/raw/산업통상부_무역구제 덤핑방지 관세 부과 현황_20251231.csv` |
| 행 수 | 275 |
| 컬럼 수 | 19 |
| 성격 | 복수 국가 행 분리 + 영문 컬럼명 표준화 + 관세 유형 파싱 완료된 이벤트 테이블 |

#### 컬럼 정의

| 컬럼 | 타입 | 결측 | 고유값 | 설명 |
|------|------|-----:|------:|------|
| `event_id` | str | 0 | 275 | 이벤트 고유 ID (`AD-XXXX-YY`) |
| `source_row_id` | int | 0 | 160 | 원천 파일 행 번호 |
| `origin_country_name_kr` | str | 0 | 27 | 부과 대상 국가명 (한국어) |
| `origin_country_iso3` | str | 3 | 25 | ISO 3166-1 alpha-3 국가 코드 |
| `product_name_kr` | str | 0 | 120 | 원천 품목명 |
| `product_name_normalized` | str | 0 | 72 | 정규화된 품목명 (분석 키) |
| `duty_text_raw` | str | 0 | 138 | 관세부과범위 원문 |
| `duty_type` | str | 0 | 6 | 관세 유형 (`ad_valorem`, `price_undertaking` 등) |
| `duty_rate_min` | float | 21 | 123 | 관세율 최솟값 (%) |
| `duty_rate_max` | float | 21 | 98 | 관세율 최댓값 (%) |
| `has_price_undertaking` | bool | 0 | 2 | 가격약속 여부 |
| `has_reference_price_diff` | bool | 0 | 2 | 기준가격 차액 방식 여부 |
| `has_partial_exclusion` | bool | 0 | 2 | 일부 국가·업체 제외 여부 |
| `start_date` | str | 0 | 129 | 부과 시작일 (YYYY-MM-DD) |
| `end_date` | str | 0 | 127 | 부과 종료일 (YYYY-MM-DD) |
| `duration_days` | int | 0 | 22 | 부과 기간(일) |
| `legal_basis` | str | 0 | 156 | 관련 법령 |
| `is_active_as_of_extract` | bool | 0 | 2 | 추출 기준일 기준 현행 여부 |
| `source_file` | str | 0 | 1 | 원천 파일명 |

---

### antidumping_normalized.csv

| 항목 | 내용 |
|------|------|
| 생성 노트북 | `notebooks/04_regulation_event_preprocessing.ipynb` |
| 원천 | `data/raw/산업통상부_무역구제 덤핑방지 관세 부과 현황_20251231.csv` |
| 행 수 | 275 |
| 컬럼 수 | 15 |
| 성격 | `regulation_events.csv`와 동일 데이터의 한국어 컬럼명 버전 |

#### 컬럼 정의

| 컬럼 | 타입 | 결측 | 고유값 | 설명 |
|------|------|-----:|------:|------|
| `원천행번호` | int | 0 | 160 | 원천 파일 행 번호 |
| `국가명_원문` | str | 0 | 53 | 원천의 복수 국가 셀 값 |
| `국가분리순번` | int | 0 | 4 | 복수 국가 중 분리 순번 |
| `국가명_정규화` | str | 0 | 27 | 분리 후 단일 국가명 |
| `품목명_원문정리` | str | 0 | 120 | 원문 품목명 공백·특수문자 정리 |
| `품목명_정규화` | str | 0 | 72 | 분석 키로 쓰는 정규화 품목명 |
| `관세부과범위_원문` | str | 0 | 138 | 관세부과범위 원문 |
| `관세유형` | str | 0 | 7 | 파싱된 관세 유형 |
| `관세율_최소` | float | 21 | 123 | 관세율 최솟값 (%) |
| `관세율_최대` | float | 21 | 98 | 관세율 최댓값 (%) |
| `부과시작일` | str | 0 | 129 | 부과 시작일 |
| `부과종료일` | str | 0 | 127 | 부과 종료일 |
| `부과기간일` | int | 0 | 22 | 부과 기간(일) |
| `관련법령` | str | 0 | 156 | 관련 법령 |
| `추출기준일_유효여부` | bool | 0 | 2 | 현행 여부 |

---

### eu_sanctions_hs6.csv

| 항목 | 내용 |
|------|------|
| 출처 | AEA Replication Package (229004-V1) `EU_sanctions_HS6.dta` 변환 |
| 원본 파일 | `EU_sanctions_HS6.dta` (Stata) |
| 행 수 | 2,304 |
| 컬럼 수 | 13 |
| 성격 | EU의 러시아 제재 대상 HS 6단위 품목 목록 및 제재 유형 분류 |

#### 컬럼 정의

| 컬럼 | 타입 | 결측 | 고유값 | 설명 |
|------|------|-----:|------:|------|
| `Code` | int | 0 | 2,304 | HS 6단위 코드 |
| `Date` | str | 0 | 11 | 제재 발효일 |
| `Winddowndate` | str | 1 | 11 | 유예기간 종료일 |
| `partially_exempt` | float | 0 | 2 | 부분 면제 여부 |
| `sanction_type` | int | 0 | 3 | 제재 유형 (1=luxury, 2=industrial, 3=dual-use) |
| `aviation` | float | 2,271 | 1 | 항공 관련 품목 여부 |
| `dual_use` | float | 1,439 | 1 | 이중용도 품목 여부 |
| `firearms` | float | 2,280 | 1 | 화기 관련 여부 |
| `industrial_cap` | float | 1,316 | 1 | 산업 제한 품목 여부 |
| `luxury` | float | 1,597 | 1 | 사치품 여부 |
| `military_tech` | float | 1,794 | 1 | 군사기술 여부 |
| `oil_exploration` | float | 2,278 | 1 | 석유 탐사 관련 여부 |
| `oil_refining` | float | 2,296 | 1 | 석유 정제 관련 여부 |

#### 제재 유형별 품목 수 (참고)

| sanction_type | 유형 | 품목 수 |
|--------------|------|--------|
| 1 | luxury (명품·사치품) | 570 |
| 2 | industrial (산업용) | 667 |
| 3 | dual-use (이중용도) | 1,067 |

---

### import_trade_df.csv

| 항목 | 내용 |
|------|------|
| 생성 노트북 | `notebooks/05_aea_replication_analysis.ipynb` |
| 원천 | 관세청 API 또는 UN Comtrade API |
| 행 수 | 15,191 |
| 컬럼 수 | 13 |
| 성격 | 수입 무역 데이터 (반덤핑 대상 품목 × 국가 × 기간) |

#### 컬럼 정의

| 컬럼 | 타입 | 결측 | 고유값 | 설명 |
|------|------|-----:|------:|------|
| `row_index` | int | 0 | 60 | 원천 행 인덱스 |
| `start_date` | float | 0 | 182 | 부과 시작일 |
| `end_date` | float | 0 | 182 | 부과 종료일 |
| `reporter` | str | 0 | 1 | 보고국 (한국) |
| `flow` | str | 0 | 1 | 무역 흐름 (수입 `M`) |
| `partner` | str | 0 | 20 | 상대국 |
| `hs_code` | int | 0 | 28 | HS 코드 |
| `product_name` | str | 0 | 84 | 품목명 |
| `tariff_scope` | str | 0 | 57 | 관세 적용 범위 |
| `quantity` | int | 0 | 11,248 | 수입 수량 |
| `value` | int | 0 | 12,069 | 수입 금액 |
| `unit_price` | float | 0 | 12,237 | 단가 |
| `is_regulated_country` | bool | 0 | 1 | 규제 대상국 여부 |

---

### product_hs_mapping.csv

| 항목 | 내용 |
|------|------|
| 생성 노트북 | `notebooks/반덤핑_HS코드_이력_매핑/HS코드_이력_매핑.ipynb` |
| 최근 업데이트 | 2026-05-20 (v2: needs_review 0개 달성) |
| 행 수 | 72 |
| 컬럼 수 | 7 |
| 성격 | 반덤핑 대상 72개 품목의 현행 HS 6단위 코드 매핑 참조 테이블 |

#### 컬럼 정의

| 컬럼 | 타입 | 결측 | 고유값 | 설명 |
|------|------|-----:|------:|------|
| `product_name_normalized` | str | 0 | 72 | 정규화된 품목명 (조인 키) |
| `hs_code` | int | 0 | 59 | 확정 HS 코드 |
| `hs_level` | float | 0 | 2 | 코드 자리수 (4.0 또는 6.0) |
| `hs_description` | str | 0 | 59 | HS 코드 영문 설명 |
| `mapping_confidence` | str | 0 | 4 | 신뢰도 (`confirmed`/`high`/`medium`/`low`) |
| `mapping_method` | str | 0 | 1 | 매핑 방법 (`web_search`) |
| `mapping_note` | str | 0 | 65 | 근거 및 주의 사항 |

#### 신뢰도 분포

| mapping_confidence | 품목 수 | 기준 |
|-------------------|--------|------|
| confirmed | 8 | 한국 반덤핑 고시·WCO에서 코드 직접 확인 |
| high | 33 | WCO 소호·EU TARIC·US HTS 교차 확인 |
| medium | 29 | 웹 검색 기반, 두께·형태 등 세부 조건에 따라 소호 달라질 수 있음 |
| low | 2 | 용도에 따라 분류 분기 가능, 수동 확인 필요 |

#### 버전 이력

| 파일 | 상태 | 비고 |
|------|------|------|
| `product_hs_mapping.csv` | 항상 최신 | — |

상세 조사 결과: `reports/09_antidumping_hs_mapping_research.md`

---

### 반덤핑\_HS코드\_검토목록.csv

| 항목 | 내용 |
|------|------|
| 생성 노트북 | `notebooks/반덤핑_HS코드_이력_매핑/HS코드_이력_매핑.ipynb` |
| 행 수 | 72 |
| 컬럼 수 | 16 |
| 성격 | 매핑 전 검토 대상 목록. 이슈 유형·권장 조치·연도별 HS 코드 후보 기록 |

#### 컬럼 정의

| 컬럼 | 타입 | 결측 | 고유값 | 설명 |
|------|------|-----:|------:|------|
| `issue_type` | str | 0 | 2 | 이슈 유형 (`missing_all`: 전체 미매핑, `partial`: 일부 개정판 누락) |
| `suggested_action` | str | 0 | 2 | 권장 조치 |
| `품목명_정규화` | str | 0 | 72 | 정규화된 품목명 |
| `품목명_원문예시` | str | 0 | 72 | 원문 품목명 예시 |
| `first_start` | str | 0 | 67 | 최초 부과 시작일 |
| `last_end` | str | 0 | 67 | 최종 부과 종료일 |
| `event_count` | int | 0 | 12 | 해당 품목의 반덤핑 이벤트 수 |
| `countries` | str | 0 | 42 | 대상 국가 목록 |
| `HS1992`~`HS2022` | float | 45 | 13 | 개정판별 HS 코드 후보 (미매핑 시 NaN) |
| `note` | float | 72 | 0 | 비고 (현재 전체 미기입) |

---

### 반덤핑\_HS코드\_이력.csv *(메인 산출물)*

| 항목 | 내용 |
|------|------|
| 생성 노트북 | `notebooks/반덤핑_HS코드_이력_매핑/HS코드_이력_매핑.ipynb` |
| 최근 업데이트 | 2026-05-20 (v2) |
| 행 수 | 504 (72품목 × 7개정판) |
| 컬럼 수 | 12 |
| 성격 | 반덤핑 대상 72개 품목의 HS 개정판(H0~H6)별 코드 이력 테이블. Issue #7 최종 산출물 |

#### 컬럼 정의

| 컬럼 | 타입 | 결측 | 고유값 | 설명 |
|------|------|-----:|------:|------|
| `품목명_정규화` | str | 0 | 72 | 정규화된 품목명 |
| `품목명_원문예시` | str | 0 | 72 | 원문 품목명 예시 |
| `hs_revision` | str | 0 | 7 | HS 개정판 식별자 (`H0`~`H6`) |
| `hs_version` | str | 0 | 7 | 개정판 명칭 (`HS1992`~`HS2022`) |
| `valid_from_year` | int | 0 | 7 | 해당 개정판 적용 시작 연도 |
| `valid_to_year` | int | 0 | 7 | 해당 개정판 적용 종료 연도 (현행은 9999) |
| `hs_code` | int | 0 | 59 | HS 코드 (해당 개정판 기준) |
| `hs_level` | float | 0 | 2 | 코드 자리수 (4.0 또는 6.0) |
| `hs_description` | str | 0 | 59 | HS 코드 영문 설명 |
| `hs_code_changed_from_prev` | float | 504 | 0 | 이전 개정판 대비 코드 변경 여부 (미기입) |
| `mapping_status` | str | 0 | 4 | 매핑 신뢰도 (`confirmed`/`high`/`medium`/`low`) |
| `note` | str | 0 | 65 | 매핑 근거 및 주의 사항 |

#### HS 개정판 타임라인

| hs_revision | hs_version | valid_from_year | valid_to_year |
|------------|-----------|----------------|--------------|
| H0 | HS1992 | 1988 | 1995 |
| H1 | HS1996 | 1996 | 2001 |
| H2 | HS2002 | 2002 | 2006 |
| H3 | HS2007 | 2007 | 2011 |
| H4 | HS2012 | 2012 | 2016 |
| H5 | HS2017 | 2017 | 2021 |
| H6 | HS2022 | 2022 | 9999 |

#### 버전 이력

| 파일 | 행 수 | mapping_status 분포 | 비고 |
|------|------|-------------------|------|
| `반덤핑_HS코드_이력_v1.csv` | 504 | needs_review 37품목 | 최초 생성본 |
| `반덤핑_HS코드_이력_v2.csv` | 504 | needs_review 0개 | product_hs_mapping 웹 검색 보완 후 재생성 |
| `반덤핑_HS코드_이력.csv` | 504 | needs_review 0개 | 항상 최신 버전 (현재 v2) |

#### 향후 보완 사항

- `hs_code_changed_from_prev` 컬럼 미기입 — WCO correlation table을 이용해 개정판 간 코드 변경 여부 자동 계산 필요
- `mapping_status=low` 2개 품목 수동 확인 필요 (`자동가이드홀 펀칭기`, `중질섬유관`)
- 개정판별 코드가 현재 모든 H0~H6에 동일하게 적용됨 — 실제로 개정판 간 코드가 다를 경우 수동 보정 필요

---

## API 기반 논리 데이터셋

### UN Comtrade 월별 대러 무역 데이터

| 항목 | 내용 |
|------|------|
| 생성 노트북 | `notebooks/03_russia_sanctions_trade_shift_analysis.ipynb` |
| 원천 | UN Comtrade API |
| 인증 | `.env`의 `COMTRADE_API_KEY` |
| 기간 | 2020-01 ~ 2024-12 |
| 보고국 | Armenia, Kazakhstan, Georgia, Turkey/Türkiye, UAE |
| 상대국 | 러시아 (`partnerCode=643`) |
| 품목 | HS 7210, HS 8542 (2단위) |
| 흐름 | 수출 `X` / 수입 `M` |
| 저장 여부 | 로컬 미저장 (노트북 재실행 시 재수집 필요) |

#### 주요 컬럼

| 컬럼 | 설명 |
|------|------|
| `reporterDesc` | 보고국명 |
| `cmdCode` | HS 품목 코드 |
| `flowCode` | 수출입 구분 |
| `refYear` | 기준 연도 |
| `refMonth` | 기준 월 |
| `primaryValue` | 분석용 금액 (USD) |
| `isReported` | 직접 보고 여부 |
| `isAggregate` | 집계 데이터 여부 |

#### 저장 권장 경로

```
data/interim/comtrade_monthly_2020_2024_russia_7210_8542.csv
data/processed/russia_trade_shift_summary_2020_2024.csv
```

---

### 관세청 품목별 국가별 수출입실적

| 항목 | 내용 |
|------|------|
| 생성 노트북 | `notebooks/02_customs_trade_api_example.ipynb` |
| 원천 | 관세청 공공데이터포털 API |
| 인증 | `.env`의 `CUSTOMS_TRADE_STATS_API_KEY` |
| 엔드포인트 | `https://apis.data.go.kr/1220000/nitemtrade/getNitemtradeList` |
| 저장 여부 | 로컬 미저장 |

#### 주요 컬럼

| 컬럼 | 설명 |
|------|------|
| `year` | 기준 연월 |
| `statCdCntnKor1` | 국가명 |
| `hsCd` | HS 코드 |
| `impDlr` | 수입 금액 (USD) |
| `expDlr` | 수출 금액 (USD) |
| `balPayments` | 무역수지 |

#### 저장 권장 경로

```
data/interim/customs_trade_<hs_code>_<country>_<start>_<end>.csv
```

---

## 관리 원칙

- 원천 파일(`data/raw/`)은 수정하지 않는다.
- `data/interim/`·`data/processed/`는 gitignore 대상으로, 로컬 또는 외부 저장소에서 버전 관리한다.
- 이력 테이블 등 중요 중간 산출물은 `_v1`, `_v2` 접미사로 스냅샷을 보존하고, 무접미사 파일은 항상 최신 버전을 유지한다.
- 한국어 CSV 저장 시 `encoding="utf-8-sig"`를 사용해 Windows Excel 호환성을 확보한다.
- API 재수집 결과에는 수집 시점·파라미터·실패 국가를 함께 기록한다.
