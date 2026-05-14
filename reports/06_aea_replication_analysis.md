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

| sanction_type | 그룹 | 포함 카테고리 |
|---------------|------|--------------|
| 0 | 기타 제재 | 위 세 그룹에 해당하지 않는 제재 품목 |
| 1 | 명품(Luxury) | `luxury` |
| 2 | 산업(Industrial) | `aviation`, `industrial_cap`, `oil_exploration`, `oil_refining` |
| 3 | 이중용도(Dual-use) | `dual_use`, `firearms`, `military_tech` ← **우회 탐지 핵심** |

산출물: `data/interim/eu_sanctions_hs6.csv`

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

## 4. 다음 단계

- [ ] `eu_sanctions_hs6.csv` 기준으로 수집 대상 HS6 코드 확정
- [ ] dual-use(`sanction_type=3`) 품목 우선 수집 (우회 탐지 핵심)
- [ ] UN Comtrade에서 CCA3 → 러시아 수출 데이터 HS6 단위로 재수집
- [ ] 제재 전후 비교 + 제재 품목 여부 결합 → semi-label 생성
- [ ] DiD feature(`months_since_sanction`, `is_sanctioned` 등) 피처 엔지니어링
