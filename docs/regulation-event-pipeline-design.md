# 규제 이벤트 기반 우회무역 분석 데이터 설계

## 목적

현재 `data/raw`에 있는 산업통상부 덤핑방지 관세 부과 현황 데이터는 우회무역을 직접 탐지할 수 있는 월별 무역 시계열이 아니라, 한국이 특정 국가와 품목에 대해 규제를 부과한 이력 데이터이다.

따라서 이 데이터는 기획안의 탐지 모델에서 다음 역할을 맡는다.

- 규제 충격 시점 정의
- 분석 대상 국가·품목 후보군 생성
- 관세청/UN Comtrade API 수집 파라미터 생성
- 제재 전후 비교 윈도우 설정
- 우회무역 탐지 결과의 이벤트 라벨 또는 기준 테이블 제공

이 설계문서는 raw CSV를 `regulation_events` 테이블로 정규화하고, 후속 무역통계 수집·탐지 지표 계산과 연결하는 구조를 정의한다.

## 입력 데이터

| 항목 | 내용 |
|---|---|
| 파일 | `data/raw/산업통상부_무역구제 덤핑방지 관세 부과 현황_20251231.csv` |
| 인코딩 | CP949 |
| 행 수 | 160 |
| 컬럼 | `국가명`, `품목`, `관세부과범위`, `부과시작일`, `부과종료일`, `관련법령` |
| 성격 | 한국의 덤핑방지 관세 부과 이력 |

## 현재 데이터로 가능한 것과 불가능한 것

### 가능한 것

- 어떤 국가가 규제 대상이었는지 확인
- 어떤 품목이 규제 대상이었는지 확인
- 규제 시작일과 종료일을 이용해 이벤트 기간 정의
- 현재 유효한 규제 조치 목록 생성
- 국가·품목별 반복 규제 여부 집계
- 후속 무역통계 수집 대상 후보 생성

### 불가능한 것

- 우회무역 발생 여부 직접 판정
- 월별 수입량·수입액 급증 여부 계산
- 제3국 경유 재수출 비율 계산
- 국가 간 단가 비교
- HS 6단위 품목 전이 분석

위 항목들은 관세청 품목별 수출입실적, UN Comtrade, HS 코드 매핑, WTO 관세율 데이터가 추가로 필요하다.

## 전체 파이프라인

```text
data/raw/덤핑방지 관세 CSV
        |
        v
data/interim/regulation_events.csv
        |
        v
data/processed/regulation_event_candidates.csv
        |
        +--> 관세청 API 수집 파라미터
        +--> UN Comtrade API 수집 파라미터
        +--> 제재 전후 분석 윈도우
        |
        v
무역 시계열 결합
        |
        v
SR / Growth / CV / VAI / ReExport / PR / DPR / TD 지표 계산
```

## 산출 테이블 설계

### 1. `regulation_events`

저장 위치:

```text
data/interim/regulation_events.csv
```

역할:

raw CSV를 분석 가능한 long format으로 정규화한 이벤트 테이블이다. `국가명`에 복수 국가가 들어 있는 경우 국가별 행으로 분리한다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `event_id` | string | 원천 행과 국가 분리를 반영한 고유 이벤트 ID |
| `source_row_id` | int | raw CSV 원본 행 번호 |
| `origin_country_name_kr` | string | 덤핑방지관세 대상 원산지/수출국명, 한국어 |
| `origin_country_iso3` | string | 덤핑방지관세 대상 원산지/수출국 ISO3 코드, 매핑 가능 시 입력 |
| `product_name_kr` | string | 원천 품목명 |
| `product_name_normalized` | string | 괄호, 재심 표기 등을 정리한 품목명 |
| `duty_text_raw` | string | 원천 `관세부과범위` |
| `duty_type` | string | `ad_valorem`, `price_undertaking`, `reference_price_diff`, `partial_exclusion`, `mixed`, `unknown` |
| `duty_rate_min` | float | 숫자 관세율 최소값 |
| `duty_rate_max` | float | 숫자 관세율 최대값 |
| `has_price_undertaking` | bool | 가격약속 포함 여부 |
| `start_date` | date | 부과 시작일 |
| `end_date` | date | 부과 종료일 |
| `duration_days` | int | 부과 기간 |
| `legal_basis` | string | 관련 법령 |
| `is_active_as_of_extract` | bool | 파일 기준일 또는 분석 기준일 현재 유효 여부 |
| `source_file` | string | 원천 파일명 |

#### `event_id` 규칙

```text
AD-{source_row_id:04d}-{origin_country_seq:02d}
```

예:

```text
AD-0001-01
AD-0001-02
```

### 2. `product_hs_mapping`

저장 위치:

```text
data/interim/product_hs_mapping.csv
```

역할:

raw 데이터에는 HS 코드가 없으므로 품목명과 HS 후보 코드를 연결하는 수동/반자동 매핑 테이블이 필요하다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `product_name_normalized` | string | 정규화 품목명 |
| `hs_code` | string | HS 코드 |
| `hs_level` | int | HS 코드 자릿수, 4 또는 6 권장 |
| `hs_description` | string | HS 품목 설명 |
| `mapping_confidence` | string | `high`, `medium`, `low` |
| `mapping_method` | string | `manual`, `keyword`, `official_reference` |
| `mapping_note` | string | 판단 근거 |

주의:

- 기획안의 HS 4단위-6단위 전이 분석을 하려면 최소 HS 6단위가 필요하다.
- 품목명이 넓은 경우에는 하나의 품목명이 여러 HS 코드로 매핑될 수 있다.
- 자동 키워드 매핑은 후보 생성까지만 사용하고, 최종 분석 전 수동 검토가 필요하다.

### 3. `regulation_event_candidates`

저장 위치:

```text
data/processed/regulation_event_candidates.csv
```

역할:

규제 이벤트와 HS 매핑을 결합하여 실제 API 수집과 탐지 지표 계산에 사용할 후보 테이블이다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `candidate_id` | string | 이벤트-HS 조합 고유 ID |
| `event_id` | string | `regulation_events.event_id` |
| `origin_country_name_kr` | string | 덤핑방지관세 대상 원산지/수출국명 |
| `origin_country_iso3` | string | ISO3 국가 코드 |
| `product_name_normalized` | string | 정규화 품목명 |
| `hs_code` | string | 분석 대상 HS 코드 |
| `hs_level` | int | HS 코드 자릿수 |
| `start_date` | date | 규제 시작일 |
| `end_date` | date | 규제 종료일 |
| `pre_window_start` | date | 규제 전 비교 시작일 |
| `pre_window_end` | date | 규제 전 비교 종료일 |
| `post_window_start` | date | 규제 후 비교 시작일 |
| `post_window_end` | date | 규제 후 비교 종료일 |
| `candidate_priority` | string | `high`, `medium`, `low` |
| `candidate_reason` | string | 후보 선정 사유 |

기본 윈도우:

- `pre_window_start`: 규제 시작일 기준 24개월 전
- `pre_window_end`: 규제 시작일 전월
- `post_window_start`: 규제 시작월
- `post_window_end`: 규제 시작일 기준 24개월 후 또는 종료일 중 빠른 날짜

## 전처리 규칙

### 국가명 분리

`국가명` 컬럼은 쉼표로 여러 국가가 묶여 있을 수 있다.

예:

```text
중국,인니,대만
대만,태국,아랍에미레이트
```

처리:

1. 쉼표 기준 분리
2. 앞뒤 공백 제거
3. 국가명 표준화
4. 국가별로 행 확장

국가명 표준화 예시:

| 원천 값 | 표준 값 |
|---|---|
| `인니` | `인도네시아` |
| `말레이지아` | `말레이시아` |
| `미국캐나다` | 원천 오류 가능성 검토 후 `미국`, `캐나다` 분리 여부 결정 |
| `아랍에미레이트` | `아랍에미리트` 또는 ISO 기준 UAE로 통일 |

### 품목명 정규화

처리:

1. 앞뒤 공백 제거
2. 재심 표기 분리
3. 괄호 안 부가 설명은 보존하되 검색용 이름에서는 제거
4. 대소문자 통일이 필요한 영문 품목명 정리

예:

| 원천 품목명 | 정규화 품목명 | 비고 |
|---|---|---|
| `H 형강(1차재심)` | `H 형강` | 재심 표기 제거 |
| `초산에틸(1차재심)` | `초산에틸` | 재심 표기 제거 |
| `폴리에틸렌테레프탈레이트(pet) 필름` | `폴리에틸렌테레프탈레이트 필름` | 검색용 정규화 |

### 관세부과범위 파싱

`관세부과범위`는 숫자 관세율과 텍스트 조치가 혼재한다.

예:

```text
40.46~54.28
66.11,가격약속
기준가격과 수입가격의 차액
일부부과제외
가격약속
```

처리:

- 숫자 범위가 있으면 `duty_rate_min`, `duty_rate_max` 추출
- `가격약속` 포함 시 `has_price_undertaking=True`
- `기준가격과 수입가격의 차액`은 `reference_price_diff`
- `일부부과제외`는 `partial_exclusion`
- 숫자와 텍스트가 함께 있으면 `mixed`

## 기획안 지표와의 연결

| 지표 | `regulation_events` 역할 | 추가 필요 데이터 |
|---|---|---|
| SR | 규제국 A, 품목 p, 규제 시작일 제공 | 한국의 국가별 월별 수입량 |
| Growth | 제3국 후보 분석 기준일 제공 | 관세청 월별 수입량 |
| CV | 이벤트 전후 윈도우 제공 | 관세청 월별 수입량 |
| VAI | Growth/CV 계산 대상 후보 제공 | 관세청 월별 수입량 |
| ReExport | 규제 품목과 후보국 제공 | UN Comtrade의 제3국 수입·수출 |
| PR | 규제국 A와 품목 p 제공 | 수입 금액, 수입 중량 |
| DPR | 제3국 후보와 품목 p 제공 | UN Comtrade 국가별 수출 단가 |
| TD | 반덤핑 관세율 제공 | 일반 관세율/WTO 관세율 |

## 후보 우선순위 규칙

초기 분석에서는 모든 이벤트를 다루기보다 모델 검증 가능성이 높은 이벤트를 우선 선택한다.

### High

- 현재 유효한 조치
- 관세율 숫자 추출 가능
- 품목-HS 코드 매핑 신뢰도 `high`
- 규제 대상국이 중국, 일본, 베트남, 인도 등 주요 교역국
- 철강, 화학, 필름, 합판 등 반복 규제 품목군

### Medium

- 종료된 지 오래되지 않은 조치
- HS 매핑 신뢰도 `medium`
- 관세율은 없지만 가격약속 등 명확한 규제 형태 존재

### Low

- HS 매핑 불확실
- 품목명이 지나치게 포괄적
- 가격약속 또는 일부부과제외만 있어 관세 격차 계산이 어려움
- 종료된 지 오래되어 최근 무역 패턴과 연결성이 낮음

## 후속 API 수집 설계

### 관세청 API

목적:

한국 기준으로 규제국과 제3국으로부터의 품목별 월별 수입량·수입액을 수집한다.

필요 파라미터:

| 파라미터 | 출처 |
|---|---|
| `hsSgn` | `regulation_event_candidates.hs_code` |
| `cntyCd` | 국가 코드 매핑 테이블 |
| `strtYymm` | `pre_window_start` |
| `endYymm` | `post_window_end` |

권장 저장 경로:

```text
data/interim/customs_trade_<candidate_id>.csv
```

### UN Comtrade API

목적:

규제 대상국, 제3국, 한국 간 무역 흐름과 제3국의 재수출 가능성을 확인한다.

수집 축:

- 규제 대상국 A -> 제3국 B
- 제3국 B -> 한국
- 제3국 B -> 세계
- 제3국 B의 세계 수입

권장 저장 경로:

```text
data/interim/comtrade_reexport_<candidate_id>.csv
```

## 구현 모듈 설계

### `src/data/regulation_events.py`

권장 함수:

```python
def load_raw_antidumping(path: str) -> pd.DataFrame:
    """CP949 원천 CSV를 로드한다."""

def normalize_country_names(df: pd.DataFrame) -> pd.DataFrame:
    """복수 국가명을 분리하고 표준 국가명 컬럼을 만든다."""

def normalize_product_names(df: pd.DataFrame) -> pd.DataFrame:
    """재심 표기와 괄호 설명을 정리한 품목명 컬럼을 만든다."""

def parse_duty_scope(df: pd.DataFrame) -> pd.DataFrame:
    """관세부과범위에서 관세율과 조치 유형을 추출한다."""

def build_regulation_events(raw_df: pd.DataFrame) -> pd.DataFrame:
    """정규화된 regulation_events 테이블을 생성한다."""

def build_event_candidates(
    events: pd.DataFrame,
    product_hs_mapping: pd.DataFrame,
) -> pd.DataFrame:
    """HS 매핑을 결합하여 API 수집 후보 테이블을 생성한다."""
```

### 테스트 설계

테스트 파일:

```text
tests/test_regulation_events.py
```

주요 테스트:

- CP949 CSV 로드 가능 여부
- 복수 국가 분리 여부
- `인니` 등 국가명 표준화 여부
- 관세율 범위 파싱 여부
- `가격약속`, `일부부과제외`, `기준가격과 수입가격의 차액` 분류 여부
- `event_id` 고유성
- 날짜 컬럼 변환 및 윈도우 생성 여부

## 검증 산출물

초기 구현 후 다음 요약표를 확인한다.

| 산출물 | 확인 내용 |
|---|---|
| 국가별 이벤트 수 | 반복 규제 대상국 확인 |
| 품목별 이벤트 수 | 반복 규제 품목군 확인 |
| 연도별 신규 이벤트 수 | 규제 강화 시점 확인 |
| 현재 유효 이벤트 목록 | 우선 분석 후보 확인 |
| HS 매핑 누락 품목 목록 | 수동 보강 대상 확인 |

## 주요 리스크

- raw 데이터에 HS 코드가 없어 품목-HS 매핑 품질이 전체 분석 품질을 좌우한다.
- `관세부과범위`가 비정형 텍스트라 관세율 파싱 결과를 수동 검증해야 한다.
- 국가명 표기가 한국어 약칭과 비표준 표기를 포함한다.
- 반덤핑 관세율만으로는 TD를 완성할 수 없으며 일반 실행 관세율이 별도로 필요하다.
- 이벤트가 오래된 경우 최근 무역 데이터와 직접 연결하기 어렵다.

## 1차 구현 범위

1차 구현은 우회무역 탐지 모델 전체가 아니라 이벤트 테이블 생성까지로 제한한다.

포함:

- raw CSV 로드
- 국가명 분리 및 표준화
- 품목명 정규화
- 관세부과범위 파싱
- `regulation_events.csv` 생성
- 기초 집계표 생성

제외:

- HS 코드 자동 확정
- 관세청/Comtrade API 대량 수집
- SR, VAI, ReExport, PR, DPR 계산
- 모델링 또는 스코어링

이 범위를 먼저 완료한 뒤 HS 매핑 품질을 확인하고 API 수집 단계로 넘어간다.

