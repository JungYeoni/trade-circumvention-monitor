# HS 코드 개정판 이력 참고 자료

**관련 이슈**: #7  
**관련 노트북**: `notebooks/05_반덤핑_HS코드_이력_매핑/HS코드_이력_매핑.ipynb`

---

## 개요

반덤핑 규제 기간(최장 30년 이상)에 걸쳐 HS 코드는 여러 차례 개정됐다.  
UN Comtrade에서 연도별 데이터를 수집할 때 해당 연도에 맞는 개정판 코드를 써야 하므로,  
품목별 HS 코드 변경 이력을 별도 테이블로 관리한다.

---

## HS 개정판 타임라인

WCO(World Customs Organization)는 약 5년 주기로 HS를 개정한다.  
개정 시 일부 품목의 6단위 코드가 변경되거나 신설·폐지된다.

| 개정판 | 컬럼명 | UN Comtrade 코드 | 적용 연도 |
|--------|--------|-----------------|----------|
| HS 1988/1992 | `HS1992` | `H0` | ~1995 |
| HS 1996 | `HS1996` | `H1` | 1996~2001 |
| HS 2002 | `HS2002` | `H2` | 2002~2006 |
| HS 2007 | `HS2007` | `H3` | 2007~2011 |
| HS 2012 | `HS2012` | `H4` | 2012~2016 |
| HS 2017 | `HS2017` | `H5` | 2017~2021 |
| HS 2022 | `HS2022` | `H6` | 2022~ |

---

## 참고 자료

### 1. WCO — HS 공식 명세 및 개정 이력

- **사이트**: https://www.wcoomd.org/en/topics/nomenclature/instrument-and-tools/hs-nomenclature-2022-edition.aspx
- **내용**: HS 각 개정판의 공식 명세서, 개정판 간 변경 품목 목록(Correlation Tables) 제공
- **Correlation Tables**: 이전 개정판 코드 → 신규 개정판 코드 매핑표. 코드 변경 여부 확인에 직접 활용 가능

### 2. UN Comtrade — 분류 코드 체계

- **사이트**: https://comtradeplus.un.org
- **내용**: API 호출 시 `classificationCode` 파라미터에 `H0`~`H6`를 지정해 원하는 개정판 기준 데이터 수집
- **주의**: 국가마다 보고 기준 개정판이 다를 수 있음. `classificationSearchCode=HS`로 통일 검색 가능

### 3. 관세청 HS 코드 조회 시스템

- **사이트**: https://unipass.customs.go.kr/clip/index.do
- **내용**: 한국 관세청의 품목 분류 조회 서비스. 품목명으로 현행 HS 코드 검색 가능
- **활용**: 반덤핑 품목명 → 현재 HS 코드(HS2022 기준) 확인 시 1차 참고

### 4. 관세청 HS 코드 품목분류 변경 이력

- **사이트**: https://www.customs.go.kr (품목분류 → 품목분류 변경 이력)
- **내용**: 특정 HS 코드가 개정판 전환 시 어떤 코드로 바뀌었는지 이력 조회
- **활용**: `HS_코드_이력_매핑.csv`의 개정판별 코드 변경 여부(`hs_code_changed_from_prev`) 기입 시 참고

### 5. WCO HS Correlation Tables (직접 참고 가능 문서)

각 개정판 전환 시 WCO가 공식 배포하는 변경 목록:

| 전환 구간 | 문서명 |
|-----------|--------|
| HS2017 → HS2022 | Correlation Table HS2017-HS2022 |
| HS2012 → HS2017 | Correlation Table HS2012-HS2017 |
| HS2007 → HS2012 | Correlation Table HS2007-HS2012 |
| HS2002 → HS2007 | Correlation Table HS2002-HS2007 |

WCO 회원국(한국 포함)은 관세청을 통해 이 문서에 접근 가능하며,  
일부는 학술·정책 목적으로 공개 배포된 버전도 존재한다.

---

## 코드 활용 방법

노트북에서 정의한 딕셔너리를 사용해 연도 → 개정판 코드를 자동으로 조회한다.

```python
HS_VERSION_TO_COMTRADE = {
    "HS1992": "H0",
    "HS1996": "H1",
    "HS2002": "H2",
    "HS2007": "H3",
    "HS2012": "H4",
    "HS2017": "H5",
    "HS2022": "H6",
}

HS_VERSION_YEARS = {
    "HS1992": (1988, 1995),
    "HS1996": (1996, 2001),
    "HS2002": (2002, 2006),
    "HS2007": (2007, 2011),
    "HS2012": (2012, 2016),
    "HS2017": (2017, 2021),
    "HS2022": (2022, 9999),
}

# 예: 2005년 데이터 수집 시 어떤 개정판 코드 써야 하는지
year = 2005
hs_version = next(v for v, (s, e) in HS_VERSION_YEARS.items() if s <= year <= e)
comtrade_code = HS_VERSION_TO_COMTRADE[hs_version]  # "H2"
```

---

## 주의사항

- UN Comtrade는 보고국이 사용한 개정판 기준으로 데이터를 저장한다. 같은 연도라도 국가마다 다른 개정판을 쓸 수 있다.
- 한 품목이 개정판 전환 시 코드가 바뀌지 않는 경우도 많다. Correlation Table에서 변경 여부를 반드시 확인해야 한다.
- 반덤핑 규제 기간이 1989년부터 시작되는 경우 `HS1992(H0)` 이전 데이터가 필요할 수 있으나, UN Comtrade는 사실상 1990년대 초부터 데이터를 제공한다.

---

## 작업 결과 (2026-05-15)

### 활성 규제 품목 HS 코드 확인 결과

웹 검색(WCO, tariffnumber.com, credlix.com 등) 및 한국 반덤핑 고시 교차 확인으로 아래 7개 품목의 HS 코드를 확정했다.

| 품목명 | HS 코드 | 설명 | 참고 출처 |
|--------|---------|------|----------|
| 도공 인쇄용지 | 481014 | Coated paper, sheets | 한국 반덤핑 고시 확인 |
| 부틸글리콜에테르 | 290943 | Monobutyl ethers of ethylene glycol | WCO HS2022 Ch.29 |
| 수산화알루미늄 | 281830 | Aluminium hydroxide | WCO HS2022 Ch.28 |
| 이음매없는동관 | 741110 | Tubes and pipes of refined copper | WCO HS2022 Ch.74 |
| 인쇄제판용 평면모양 사진 플레이트 | 370130 | Photographic plates >255mm | 한국 반덤핑 고시 확인 |
| 차아황산소다 | 283110 | Dithionites and sulphoxylates of sodium | WCO HS2022 Ch.28 |
| 폴리에스테르 장섬유 완전연신사 | 540247 | Polyester FDY | 한국 반덤핑 고시 확인 |

### 매핑 현황

- 전체 품목: 72개
- HS 코드 확인 완료: 35개 (48.6%)
- 수동 입력 필요: 37개 (51.4%) — 대부분 종료된 규제 품목
