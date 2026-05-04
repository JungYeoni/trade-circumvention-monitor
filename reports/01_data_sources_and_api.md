# 데이터 소스 및 API 정리

## 목적

프로젝트는 러시아 제재 이후 제3국을 경유한 무역 우회 가능성을 탐지하기 위해 두 종류의 무역 데이터를 사용한다.

- UN Comtrade API: 국가 간 품목별 수출입 흐름을 국제 기준으로 수집
- 관세청 품목별 국가별 수출입실적 API: 한국 기준 품목·국가별 수출입 실적을 월별로 확인

## UN Comtrade API

확인 노트북: `notebooks/UN Comtrade.ipynb`, `notebooks/제재_이후_특정_제_3국의_대리_수출이_구조적으로_증가했는가.ipynb`

### 주요 파라미터

| 파라미터 | 의미 | 사용 예 |
|---|---|---|
| `typeCode` | 데이터 유형 | `C`: 상품 |
| `freqCode` | 빈도 | `A`: 연간, `M`: 월별 |
| `period` | 기간 | `2020,2021`, `202401,202402` |
| `reporterCode` | 보고국 | 베트남 `704`, 아르메니아 `51` 등 |
| `partnerCode` | 상대국 | 한국 `410`, 러시아 `643` |
| `cmdCode` | HS 품목 코드 | 철강 `72`, 평판압연철강 `7210`, 반도체 `8542` |
| `flowCode` | 무역 흐름 | `X`: 수출, `M`: 수입 |
| `clCode` | 품목 분류 | `HS` |

### 분석용 핵심 컬럼

| 컬럼 | 의미 | 분석상 사용 |
|---|---|---|
| `reporterDesc` | 보고국명 | 국가별 비교 |
| `partnerDesc` | 상대국명 | 대러 수출 여부 확인 |
| `cmdCode` | HS 코드 | 품목별 분석 |
| `flowCode` | 수출입 구분 | 수출 `X` 중심 분석 |
| `refYear`, `refMonth` | 기준 연월 | 월별 시계열 구성 |
| `primaryValue` | 주요 금액 | 수출입 금액 지표 |
| `isReported` | 직접 보고 여부 | 데이터 출처 신뢰도 판단 보조 |
| `isAggregate` | 집계 여부 | 품목 집계 수준 판단 |

### 수집 로직

`src/data/comtrade_client.py`의 `collect_russia_trade()`는 다음 기준으로 월별 데이터를 수집한다.

- 대상 상대국: 러시아, `partner_code="643"`
- 대상 흐름: 기본값 `flows="M,X"`로 수입과 수출 모두 수집
- 대상 품목: 쉼표 구분 HS 코드, 예: `7210,8542`
- 대상 연도: 2020-2024
- 국가/연도별 데이터가 없거나 오류가 있으면 경고 출력 후 건너뜀

## 관세청 품목별 국가별 수출입실적 API

확인 노트북: `notebooks/관세청_수출입실적(GW).ipynb`

### 주요 파라미터

| 파라미터 | 의미 | 사용 예 |
|---|---|---|
| `serviceKey` | 공공데이터포털 인증키 | `.env`의 `CUSTOMS_TRADE_STATS_API_KEY` |
| `strtYymm` | 시작년월 | `202405` |
| `endYymm` | 종료년월 | `202604` |
| `hsSgn` | HS 품목코드 | `1001999090` |
| `cntyCd` | 국가코드 | 미국 `US` |

### 응답 컬럼

| 컬럼 | 의미 |
|---|---|
| `year` | 기간 |
| `statCdCntnKor1` | 국가명 |
| `statCd` | 국가코드 |
| `statKor` | 품목명 |
| `hsCd` | HS 코드 |
| `impDlr`, `expDlr` | 수입·수출 금액 |
| `impWgt`, `expWgt` | 수입·수출 중량 |
| `balPayments` | 무역수지 |

### 확인된 기능

노트북에서 `get_trade_data()` 함수가 작성되어 있다.

- 조회 기간이 12개월을 초과하면 자동으로 기간을 분할
- `YYYYMM` 날짜 형식 검증
- HTTP 오류, XML 파싱 오류, API 오류 코드 처리
- 총계 행 제외 옵션 제공
- 필요한 컬럼 선택 및 컬럼명 변경 가능

## 환경 변수

API 키는 `src/config.py`에서 `.env`를 통해 로드한다.

```text
COMTRADE_API_KEY=...
CUSTOMS_TRADE_STATS_API_KEY=...
```

