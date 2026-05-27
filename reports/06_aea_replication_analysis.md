# AEA 논문 Replication Package 분석 (229004-V1)

**관련 이슈**: #6  
**패키지 경로**: `229004-V1/`

---

## 개요

AEA 게재 논문의 공식 replication package를 분석하여 아래 세 가지를 프로젝트에 반영한다.

1. `EU_sanctions_HS6.dta` → EU 제재 품목 HS6 리스트 추출 및 라벨링 기준 수립
2. 비정상 수출 산출 로직 파악 → semi-label 정의 근거
3. DiD 추정 구조 파악 → feature 설계 참고

**논문 대상**: 2022년 러시아 제재 이후 EU/UK → 아르메니아·카자흐스탄·키르기스스탄(CCA3) 우회 수출 패턴을 HS6 월별 양자 수출 데이터로 분석

---

## 0. 패키지 구성 및 각 파일 역할

### 폴더 구조

```
229004-V1/
├── master code.do          ← 전체 실행 진입점
├── README.pdf
├── Raw-data/               ← 3개 파일만 포함 (Comtrade 원본 CSV는 미포함)
│   ├── EU_sanctions_HS6.dta       ✅ 제재 품목 리스트 (우리 분석 완료)
│   ├── COMTRADE partners.dta      ✅ 국가코드 → 국가명 매핑
│   └── COMTRADE reporters.dta     ✅ 국가코드 → 국가명 매핑
├── Do-files/               ← Stata 코드 5개 전부 있음
│   ├── Clean monthly data.do
│   ├── Clean annual data.do
│   ├── Figure 1.do
│   ├── Figure 2.do
│   └── Figure 3.do
├── Figures/                ← 결과 Excel (코드 없이도 최종 수치 확인 가능)
│   ├── Figure 1.xlsx
│   ├── Figure 2.xlsx
│   └── Figure 3.xlsx
├── Clean-data/             ← 비어있음 (원본 CSV 있어야 생성됨)
└── Working-data/           ← 비어있음 (중간 산출물)
```

### `master code.do` — 전체 실행 진입점

연구자가 본인 컴퓨터 경로만 입력하면 전체 분석이 자동으로 실행되는 파일이다.  
Python의 `main.py`에 해당한다.

```stata
global RAWDATA   = "$PROJ/Raw-data"
global CLEANDATA = "$PROJ/Clean-data"
global FIGURES   = "$PROJ/Figures"

do "$CODE/Clean monthly data.do"   ← 월별 데이터 정제
do "$CODE/Clean annual data.do"    ← 연간 데이터 정제
do "$CODE/Figure 1.do"             ← Figure 생성
do "$CODE/Figure 2.do"
do "$CODE/Figure 3.do"
```

`do` 명령어는 Python의 `exec()`처럼 다른 파일을 불러와 실행한다.

### `Clean monthly data.do` — 원본 CSV → Stata 포맷 변환 (월별)

두 개의 원본 CSV를 정제한다. 원본 CSV는 패키지에 미포함(UN Comtrade 직접 다운로드 필요).

| 원본 파일 | 내용 | 산출물 |
|-----------|------|--------|
| `monthly_trade_data.csv` | EU/UK → 수신국 월별 수출 | `Clean-data/monthly_trade_data.dta` |
| `CCA3 exports.csv` | CCA3 → 수신국 월별 수출 | `Clean-data/CCA3 exports.dta` |

공통 처리: `partner2code == 0` 필터(직접 양자 무역만), HS6 코드 앞자리 0 처리(5자리→6자리), 국가명 merge.

### `Clean annual data.do` — "Lost in Transit" 데이터셋 생성 (핵심)

논문의 핵심 방법론을 구현하는 파일이다.

**아이디어**: 수출국 신고액과 수입국 신고액의 차이로 우회 규모를 추정한다.

```
EU가 "X국에 Y품목 $100 수출" 신고
         ↕ 비교
X국이 "EU로부터 Y품목 $60 수입" 신고
→ $40 차이 = 제3국(러시아)으로 우회된 물량 추정
```

**처리 흐름**:
1. `full_annual_exports.csv` → 수출자 신고 데이터 정제
2. `full_annual_imports.csv` → 수입자 신고 데이터 정제
3. `(수출국, 수입국, HS6, 연도)` 기준 merge
4. 양쪽 모두 신고가 있는 쌍만 유지 (한쪽만 있으면 제외)
5. 산출물: `Clean-data/Lost in transit annual.dta`

### `Figure 1.do` — EU/UK의 대러시아·CCA3 수출 시계열

- **상단**: EU/UK → 러시아 월별 수출 (제재 유형 4그룹별)
- **하단**: EU/UK → CCA3 월별 수출 (제재 유형 4그룹별)

목적: 2022년 2월 제재 이후 러시아 직접 수출은 줄고 CCA3 우회 수출은 늘었는지 시각화.

### `Figure 2.do` — CCA3 → 러시아 재수출 시계열

CCA3가 EU 제재 품목을 러시아로 얼마나 재수출했는지 시계열 플롯.  
조지아 제외(결측 과다 — 우리 노트북 03과 동일한 판단).

### `Figure 3.do` — 수출자/수입자 신고 불일치 분석 (DiD 핵심)

"Lost in transit" 비율을 제재 전후로 비교한다.

```
log(수입자 신고액 / 수출자 신고액)
  → 정상 ≈ 0
  → 제재 후 dual-use 품목에서 이 값이 커짐
    = 실제로 더 많이 들어갔다 = 우회무역 증거
```

3개 그룹으로 나눠 비교:
1. **CCA3** — 제재 유형 4그룹으로 세분화
2. **기타 육로국가** (아제르바이잔·벨라루스·중국·몽골 등) — 전체 합산
3. **나머지 세계** — 전체 합산

### 데이터 가용성 요약

| 파일 | 포함 여부 | 비고 |
|------|-----------|------|
| `EU_sanctions_HS6.dta` | ✅ | 우리 분석 완료 → `eu_sanctions_hs6.csv` |
| `COMTRADE partners/reporters.dta` | ✅ | 국가코드 매핑용 |
| `monthly_trade_data.csv` | ❌ | UN Comtrade 직접 다운로드 필요 |
| `CCA3 exports.csv` | ❌ | UN Comtrade 직접 다운로드 필요 |
| `full_annual_exports/imports.csv` | ❌ | UN Comtrade 직접 다운로드 필요 |
| `Figures/*.xlsx` | ✅ | 최종 결과 수치 바로 확인 가능 |

---

## 1. EU 제재 품목 HS6 리스트 (`EU_sanctions_HS6.dta`)

EU Regulation 833/2014 기반의 HS6 단위 제재 품목 리스트다.  
각 HS6 코드별로 제재 카테고리(이중용도, 군사, 항공, 명품 등)가 플래그로 표시되어 있다.

### 컬럼 설명

| 컬럼 | 의미 |
|------|------|
| `Code` | HS6 코드 (6자리) |
| `Date` | 제재 발효일 |
| `Winddowndate` | 유예 기간 종료일 (wind-down period) |
| `partially_exempt` | 일부 면제 여부 |
| `Maxprice` | 가격 상한선 (해당 시) |
| `aviation` | 항공 관련 품목 |
| `dual_use` | 이중용도 품목 (민간+군사 겸용) |
| `firearms` | 화기류 |
| `industrial_cap` | 산업 설비 |
| `luxury` | 명품·사치품 |
| `military_tech` | 군사 기술 |
| `oil_exploration` | 석유 탐사 관련 |
| `oil_refining` | 석유 정제 관련 |
| `EU_sanction` | EU 제재 여부 (1=제재, NaN=비제재) |

### 규모

- 전체 HS6 코드 수: 5,369개
- EU 제재 품목 수: 2,304개
- 비제재 품목 수: 3,065개

### 제재 유형 그룹화 (Figure 2.do 방식)

논문은 제재 품목을 아래 4개 그룹으로 분류한다. 우선순위는 dual-use > industrial > luxury > 기타 순이다.

| sanction_type | 그룹 | 포함 카테고리 | 품목 수 |
|---------------|------|--------------|-------:|
| 0 | 기타 제재 | 위 세 그룹에 해당하지 않는 제재 품목 | 0 |
| 1 | 명품(Luxury) | `luxury` | 570 |
| 2 | 산업(Industrial) | `aviation`, `industrial_cap`, `oil_exploration`, `oil_refining` | 667 |
| 3 | 이중용도(Dual-use) | `dual_use`, `firearms`, `military_tech` ← **우회 탐지 핵심** | 1,067 |

### 제재 발효일 분포

2022년 2월 러시아 침공 직후(2022-02-25)에 894개로 가장 많은 품목이 제재됐으며, 이후 단계적으로 추가됐다.

| 제재 발효일 | 품목 수 |
|------------|-------:|
| 2016-12-22 | 17 |
| 2022-02-25 | 894 |
| 2022-03-15 | 583 |
| 2022-04-08 | 583 |
| 2022-06-04 | 30 |
| 2022-07-21 | 31 |
| 2022-10-06 | 30 |
| 2022-10-07 | 8 |
| 2022-12-16 | 2 |
| 2022-12-17 | 4 |
| 2023-02-25 | 122 |

### 우리 프로젝트 HS 코드 매핑 결과

현재 프로젝트 수집 대상 품목(HS 7210, HS 8542)이 EU 제재 리스트에 모두 포함되어 있음을 확인했다.

**HS 7210 계열 — 산업 제재(industrial_cap), 11개**

| HS6 코드 | 제재 발효일 | 유형 |
|---------|-----------|------|
| 721011~721090 (11개) | 2022-04-08 ~ 2023-02-25 | 산업(industrial_cap) |

- 721090(기타 아연도금 강판)만 2022-04-08, 나머지 10개(721011~721069)는 2023-02-25 제재
- 모두 `industrial_cap=1`, sanction_type=2(산업)

**HS 8542 계열 — 이중용도(dual-use), 5개**

| HS6 코드 | 제재 발효일 | 카테고리 |
|---------|-----------|---------|
| 854231 | 2022-02-25 | dual_use + industrial_cap + military_tech |
| 854232 | 2022-02-25 | dual_use + military_tech |
| 854233 | 2022-02-25 | dual_use + military_tech |
| 854239 | 2022-02-25 | dual_use + military_tech |
| 854290 | 2022-10-06 | military_tech |

- 모두 sanction_type=3(이중용도)으로 **우회 탐지 핵심 품목**

산출물: `data/interim/eu_sanctions_hs6.csv` (2,304행)

---

## 2. 비정상 수출 산출 로직 (`Clean monthly data.do` 참조)

### 논문의 데이터 전처리 흐름

1. UN Comtrade에서 EU/UK → CCA3 월별 수출 데이터 수집
2. `partner2code == 0` 필터 → 직접 양자 무역만 (3국 경유 제외)
3. HS6 코드 앞자리 0 처리 (5자리 코드에 0 추가)
4. `EU_sanctions_HS6.dta`와 merge → 각 품목의 제재 카테고리 부여
5. 제재 유형별(luxury / industrial / dual-use) 월별 수출 합계 집계

### 우리 프로젝트에 적용할 semi-label 정의 방향

| 조건 | 라벨 |
|------|------|
| 제재 품목(`EU_sanction=1`) + 제재 이후 수출 급증 | `circumvention_candidate=1` |
| 비제재 품목 또는 제재 이전 증가 | `circumvention_candidate=0` |
| 제재 품목이나 데이터 결측 과다 | `uncertain` |

---

## 3. DiD 추정 구조 (`Figure 2.do`, `Figure 3.do` 참조)

### 논문의 DiD 설계

| 항목 | 내용 |
|------|------|
| Treatment | EU 제재 품목 여부 (`EU_sanction=1`) |
| Control | 비제재 품목 (`EU_sanction=NaN`) |
| 기준 시점 | 2022년 2월 (러시아 제재 발효) |
| 대상국 | CCA3 (아르메니아·카자흐스탄·키르기스스탄) → 러시아 수출 |
| 제외국 | 조지아 (결측 과다) |
| 집계 단위 | HS6 × 월 |

### 우리 프로젝트 feature 설계 변수 후보

| 변수 | 설명 | 출처 |
|------|------|------|
| `is_sanctioned` | EU 제재 품목 여부 | `EU_sanctions_HS6.dta` |
| `sanction_type` | 제재 카테고리 (0~3) | 동 파일 |
| `sanction_date` | 제재 발효일 | 동 파일 |
| `months_since_sanction` | 제재 발효 후 경과 월 수 | 파생 변수 |
| `is_dual_use` | 이중용도 여부 | 우회 탐지 핵심 플래그 |
| `export_growth_post` | 제재 후 수출 증가율 | UN Comtrade 파생 |
| `post_pre_ratio` | 제재 전후 월평균 수출 배율 | 노트북 03 방식 재사용 |

---

## 4. 논문 vs 우리 프로젝트 비교

| 비교 항목 | AEA 논문 | 우리 프로젝트 |
|-----------|---------|-------------|
| **분석 목적** | EU/UK 수출 제재 우회 탐지 | 한국 반덤핑 관세 우회 탐지 |
| **제재 근거** | EU Regulation 833/2014 (러시아 제재) | 한국 관세청 반덤핑 관세 |
| **원산지** | EU·UK | 중국 |
| **중계국** | CCA3 (아르메니아·카자흐스탄·키르기스스탄) | 터키·카자흐스탄·아르메니아·조지아·UAE |
| **최종 목적지** | 러시아 | 한국 |
| **품목 범위** | 전체 HS6 (5,369개) | HS 7210·8542 두 품목군 |
| **데이터 출처** | 수출국 신고 + 수입국 신고 (양쪽 비교) | UN Comtrade 단방향 수출 신고 |
| **핵심 방법론** | DiD + Lost in Transit (신고 불일치) | post/pre ratio + semi-label |
| **데이터 주기** | 월별 | 월별 |
| **분석 기간** | 2022년 2월 전후 | 2020~2024년 |

### 주요 차이점 해석

1. **단방향 vs 양방향 데이터**: 논문은 수출국·수입국 신고액을 대조해 불일치분을 우회 추정치로 사용하는 반면, 우리는 UN Comtrade 수출 신고 단방향만 사용한다. 양방향 데이터를 확보하면 "Lost in Transit" 방식을 그대로 적용할 수 있다.

2. **중국은 원산지, 중계국 아님**: 논문의 CCA3는 EU 제재 품목을 러시아로 넘기는 중계국이다. 우리 프로젝트에서 중국은 반덤핑 관세 부과 대상(원산지)이므로 중계국 목록에 포함되지 않는다.

3. **품목 범위 차이**: 논문은 전체 HS6를 대상으로 제재 여부를 플래그로 처리하지만, 우리는 반덤핑 제소 품목에 한정해 수집한다. 향후 EU 제재 리스트(`eu_sanctions_hs6.csv`)와 결합해 분석 범위를 넓힐 수 있다.

---

## 5. 다음 단계

- [ ] `eu_sanctions_hs6.csv` 기준으로 수집 대상 HS6 코드 확정
- [ ] dual-use(`sanction_type=3`) 품목 우선 수집 (우회 탐지 핵심)
- [ ] UN Comtrade에서 CCA3 → 러시아 수출 데이터 HS6 단위로 재수집
- [ ] 제재 전후 비교 + 제재 품목 여부 결합 → semi-label 생성
- [ ] DiD feature(`months_since_sanction`, `is_sanctioned` 등) 피처 엔지니어링
