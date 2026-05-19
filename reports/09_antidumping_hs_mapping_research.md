# 반덤핑 HS 코드 매핑 조사 결과

## 개요

`data/interim/product_hs_mapping.csv`에 수록된 한국 반덤핑 조치 대상 품목 72개(중복 표기 포함 73행)에 대해
HS 코드 6단위 확정 및 품목명 공식 검증 작업을 수행했다. 원본 품목명은 관세청 공공데이터에서 가져온 공식 명칭이다.

---

## 분류 오류 수정 내역

기존 `needs_review` 또는 `low` 분류 항목 중 잘못된 HS 카테고리에 배정된 3건을 수정했다.

| 품목명 | 수정 전 | 수정 후 | 오류 원인 |
|--------|---------|---------|----------|
| 스테인리스스틸바 | 7219 (평판압연제품) | **722210** (봉강) | 형태 분류 오류: 판재 코드를 봉강에 적용 |
| 염화비닐중합체 후판 | 7208 (철강 후판) | **390410** (PVC 비가소화) | 소재 분류 오류: 철강 코드를 플라스틱에 적용 |
| 유리장섬유 | 7005 (판유리) | **701911** (유리섬유 초핑 스트랜드) | 형태 분류 오류: 판유리 코드를 섬유에 적용 |

---

## 신뢰도 분포 (작업 후)

| 신뢰도 | 행 수 |
|--------|------|
| confirmed | 8 |
| high | 33 |
| medium | 29 |
| low | 2 |
| needs_review | 0 |
| **합계** | **72** |

---

## 전체 매핑 결과

### confirmed (8개)

| 품목명 | HS 코드 | 영문 설명 | 근거 |
|--------|---------|----------|------|
| 도공 인쇄용지 | 481014 | Coated paper and paperboard, in sheets | 한국 반덤핑 고시 481014 직접 확인 |
| 도공인쇄용지 | 481014 | Coated paper and paperboard, in sheets | 한국 반덤핑 고시 481014 직접 확인 |
| 부틸글리콜에테르 | 290943 | Monobutyl ethers of ethylene glycol | CAS 111-76-2 (2-Butoxyethanol), 단일 소호 |
| 수산화알루미늄 | 281830 | Aluminium hydroxide | 단일 코드, 전 세계 공통 |
| 이음매없는동관 | 741110 | Tubes and pipes of refined copper | 순동 기준, 단일 코드 |
| 인쇄제판용 평면모양 사진 플레이트 | 370130 | Photographic plates, sensitised, unexposed | 한국 반덤핑 고시 3701.30 직접 확인 |
| 차아황산소다 | 283110 | Dithionites and sulphoxylates of sodium | CAS 7775-14-6 (Na₂S₂O₄), 단일 소호 |
| 폴리에스테르 장섬유 완전연신사 | 540247 | Synthetic filament yarn of polyesters, single | 한국 반덤핑 고시 5402.47 직접 확인 |

### high (33개)

| 품목명 | HS 코드 | 영문 설명 | 근거 |
|--------|---------|----------|------|
| H 형강 | 721633 | H sections of iron/steel, hot-rolled, height ≥80mm | WCO 소호 명칭 확인 |
| H형강 | 721633 | H sections of iron/steel, hot-rolled, height ≥80mm | WCO 소호 명칭 확인 |
| 공기압 전송용 밸브 | 848120 | Valves for pneumatic power transmission | EU TARIC·US HTS 교차 확인 |
| 과산화벤조일 | 291632 | Benzoyl peroxide and benzoyl chloride | WCO 체계 확인 |
| 리듐1차전지 | 850650 | Lithium cells and batteries | WCO 체계상 명확히 규정 |
| 리튬1차전지 | 850650 | Lithium cells and batteries | WCO 체계상 명확히 규정 |
| 볼베어링 | 848210 | Ball bearings | WCO 소호 명확히 규정 |
| 산업용 로봇 | 847950 | Industrial robots | WCO 소호 명시, 한국 무역위원회 반덤핑 결정문 확인 |
| 셀프복사지 | 480920 | Self-copy paper | WCO 체계 명시 |
| 소다회 | 283620 | Sodium carbonate | WCO 체계 명확히 규정 |
| 스테인레스스틸바 | 722210 | Bars and rods of stainless steel, hot-rolled | WCO 체계 확인 |
| 스테인리스 스틸바 | 722210 | Bars and rods of stainless steel, hot-rolled | 기존 7219 오류 수정 |
| 스테인리스스틸바 | 722210 | Bars and rods of stainless steel, hot-rolled | 기존 7219 오류 수정 |
| 아나타제형 이산화티타늄 | 320611 | Pigments based on titanium dioxide, ≥80% TiO₂ | WCO 체계 확인, 안료 제형 기준 |
| 아연도금철선 | 721720 | Zinc coated wire of iron or non-alloy steel | WCO 체계 확인 |
| 알루미나 시멘트 | 252340 | Aluminous cement | WCO 체계 명확히 규정 |
| 알칼리망간 건전지 | 850610 | Manganese dioxide cells and batteries | EU TARIC 확인 |
| 에탄올아민 | 292219 | Amino-alcohols, other | MEA·DEA·TEA 혼합물 포함 |
| 에틸렌-초산비닐 공중합체 | 390130 | Ethylene-vinyl acetate copolymers | WCO 소호 명확히 규정 |
| 염화콜린 | 292310 | Choline and its salts | WCO 체계 명확히 규정 |
| 일회용 포켓형 라이타 | 961310 | Pocket lighters, gas fuelled, not refillable | WCO 체계 확인 |
| 전기다리미 | 851640 | Electric smoothing irons | WCO 소호 명확히 규정 |
| 전기면도기 | 851010 | Shavers | WCO 소호 명확히 규정 |
| 정보용지 및 백상지 | 480256 | Uncoated paper and paperboard, for writing/printing | WCO 체계 확인 |
| 정제인산 | 280920 | Phosphoric acid and polyphosphoric acids | WCO 체계 명확히 규정 |
| 초산에틸 | 291531 | Ethyl acetate | WCO 소호 명확히 규정 |
| 파티클 보드 | 441011 | Particle board of wood | WCO 체계 명확히 규정 |
| 파티클보드 | 441011 | Particle board of wood | WCO 체계 명확히 규정 |
| 페로실리코망간 | 720230 | Ferro-silico-manganese | WCO 체계 명확히 규정 |
| 폴리비닐 알코올 | 390530 | Poly(vinyl alcohol) | WCO 소호 명확히 규정 |
| 폴리비닐알콜 | 390530 | Poly(vinyl alcohol) | WCO 소호 명확히 규정 |
| 폴리아세탈수지 | 390710 | Polyacetals | WCO 소호 명확히 규정 |
| 폴리에스터 장섬유 부분연신사 | 540246 | Partially oriented yarn of polyesters, single | WCO 체계 확인 |
| 폴리에스테르 장섬유 연신가공사 | 540233 | Textured yarn of polyesters | WCO 체계 확인 |

### medium (29개)

| 품목명 | HS 코드 | 영문 설명 | 주의 사항 |
|--------|---------|----------|----------|
| CD-R | 852341 | Optical discs, unrecorded | HS 2017 기준 |
| D.C.P | 283525 | Calcium hydrogenorthophosphate (dicalcium phosphate) | 사료·식품용 인산칼슘 |
| OPP필름 | 392020 | Film of polypropylene | 연신 폴리프로필렌 |
| PET수지 | 390760 | Poly(ethylene terephthalate) | PET 원료 수지 |
| PET필름 | 392062 | Film of poly(ethylene terephthalate) | — |
| PS 인쇄판 | 844250 | Plates, cylinders and other printing components | 감광 미노광 상태는 3701.30 가능 |
| 도자기질 타일 | 690721 | Ceramic flags and paving tiles, glazed | 유약 처리 기준 |
| 두꺼운 PET필름 | 392062 | Film of poly(ethylene terephthalate) | — |
| 방적용 복합호제 | 380991 | Finishing agents, dye carriers for textiles | 전분계이면 3809.10 가능 |
| 백시멘트 | 252329 | White Portland cement | — |
| 산업용 공기조절기 | 841582 | Air conditioning machines, other | 부품이면 841590 가능 |
| 석유수지 | 391110 | Petroleum resins | — |
| 스테인리스강 냉간압연제품 | 721931 | Cold-rolled stainless steel, width ≥600mm, thickness ≥3mm | 두께·폭에 따라 소호 달라짐 |
| 스테인리스강 평판압연제품 | 721911 | Hot-rolled stainless steel, width ≥600mm, thickness >10mm | 두께·압연방식에 따라 소호 달라짐 |
| 스테인리스스틸 후판 | 721911 | Hot-rolled stainless steel, width ≥600mm, thickness >10mm | 두께 10mm 초과 기준 |
| 스테인리스평판압연 | 721900 | Flat-rolled products of stainless steel (4단위) | 6단위 세분화 필요 |
| 아연도금철선 | 721720 | Zinc coated wire of iron or non-alloy steel | — |
| 알루미늄 보틀캔 | 761290 | Aluminium casks, drums, cans and similar containers | — |
| 염화비닐중합체 후판 | 390410 | Poly(vinyl chloride), not mixed | 기존 7208(철강) 오류 수정 |
| 옵셋인쇄판 | 844250 | Plates, cylinders and other printing components | — |
| 유리장섬유 | 701911 | Chopped strands of glass fibres | 기존 7005(판유리) 오류 수정 |
| 침엽수 합판 | 441231 | Plywood with outer ply of coniferous wood | — |
| 침엽수합판 | 441231 | Plywood with outer ply of coniferous wood | — |
| 크라프트지 | 480439 | Kraft paper, bleached, other | 표백 여부에 따라 480411~480439 범위 |
| 탄소강과 그밖의 합금강 열간압연 후판제품 | 720811 | Hot-rolled iron/steel flat products, thickness >10mm | 두께 10mm 초과 코일 외 기준 |
| 폴리아미드필름 | 392073 | Film of polyamides | — |
| 폴리에틸렌테레프탈레이트 필름 | 392062 | Film of poly(ethylene terephthalate) | — |
| 플로트판유리 | 700529 | Float glass, colourless, thickness >2.5mm | 색유리·특수유리는 별도 소호 |
| 합판 | 441231 | Plywood with outer ply of coniferous wood | 기타 합판은 441239 가능 |

### low (2개, 수동 확인 필요)

| 품목명 | HS 코드 | 영문 설명 | 불확실 이유 |
|--------|---------|----------|-----------|
| 자동가이드홀 펀칭기 | 846249 | Punching or notching machines, other | 인쇄·PCB 필름용 특수기계. 용도에 따라 8207(수공구), 8479(기타기계) 분기 가능 |
| 중질섬유관 | 482390 | Other articles of paper, paperboard | 경화섬유 튜브 분류 불확실. 4811·4823 범위 내 전문가 확인 필요 |

---

## 품목명 공식 검증 결과

관세청 공공데이터 원본 품목명이므로 공식 명칭은 신뢰 가능하다.
웹 검색에서 발견된 표기 차이 항목:

| 파일 내 명칭 | 외부 자료 표기 | 판단 |
|------------|-------------|------|
| H형강 | 에이치(H)형강 | 표기만 다름, 동일 품목 |
| OPP필름 | 폴리프로필렌 연신필름 | 약칭 vs 공식명, 동일 품목 |
| 도공인쇄용지 | 도공(COATED) 인쇄용지 | 표기만 다름, 동일 품목 |
| 리듐1차전지 | 리튬(Lithium) 1차전지 | "리듐"이 관세청 공식 표기일 가능성 있음 (확인 필요) |
| 유리장섬유 | 단일모드 광섬유와 별개 품목 존재 | 유리섬유(7019)와 광섬유(8544)는 별개. 원본 기재 기준으로 7019.11 유지 |

---

## 참고 자료 및 링크

### 주요 HS 코드 분류 기준

| 기관 | 자료명 | URL |
|------|--------|-----|
| WCO (세계관세기구) | HS Nomenclature 2022 Edition | https://www.wcoomd.org/en/topics/nomenclature/instrument-and-tools/hs-nomenclature-2022-edition/hs-nomenclature-2022-edition.aspx |
| WCO | HS 2017 Edition (H5) | https://www.wcoomd.org/en/topics/nomenclature/instrument-and-tools/hs_nomenclature_2017/hs_nomenclature_table_2017.aspx |
| 관세청 | 세계HS정보시스템 (UniPass) | https://unipass.customs.go.kr/clip/index.do |
| 관세청 | 관세법령정보포털 품목분류 | https://www.customs.go.kr/kcs/ad/cvpl/CvplInfoMngList.do |
| 무역위원회 (KTC) | 반덤핑 조사·결정문 | https://www.ktc.go.kr/anti/antidumping/antidumpingList.do |
| 공공데이터포털 | 무역위원회_반덤핑관세조치현황 | https://www.data.go.kr/data/15000897/fileData.do |

### HS 코드 세부 조회

| 기관 | 자료명 | URL |
|------|--------|-----|
| EU 집행위원회 | TARIC 관세 데이터베이스 | https://ec.europa.eu/taxation_customs/dds2/taric/taric_consultation.jsp |
| 미국 ITC | HTS (Harmonized Tariff Schedule) | https://hts.usitc.gov/ |
| UN 통계국 | UN Comtrade 품목 분류 조회 | https://comtradeplus.un.org/ |
| 법제처 | 관세·무역 법령 | https://www.law.go.kr/ |

### 개별 품목 검증에 활용한 화학물질 DB

| 기관 | 자료명 | URL |
|------|--------|-----|
| 미국 NLM | PubChem (CAS 번호 확인) | https://pubchem.ncbi.nlm.nih.gov/ |
| ECHA | 유럽 화학물질청 (화학물질 분류) | https://echa.europa.eu/ |

---

## 작업 이력

| 일자 | 작업 내용 |
|------|----------|
| 2026-05-20 | needs_review 38개 → 0개 완료 (웹 검색 기반 HS 6단위 확정) |
| 2026-05-20 | 분류 오류 3건 수정 (스테인리스바·PVC후판·유리장섬유) |
| 2026-05-20 | 기존 4단위 low 항목 6단위로 업그레이드 (H형강·OPP필름·PET수지 등) |
| 2026-05-20 | 품목명 관세청 공식 데이터 대조 검증 완료 |

---

## 향후 과제

- `스테인리스평판압연` (HS 7219, 4단위) → 실제 반덤핑 고시 원문에서 6단위 소호 확인 필요
- `자동가이드홀 펀칭기` (846249) → 무역위원회 결정문 원문에서 HS 코드 직접 확인 필요
- `중질섬유관` (482390) → 제조 공정·물성 기준으로 4811 vs 4823 전문가 확인 필요
- `리듐1차전지` 표기 → "리듐"이 관세청 고시 원문 표기인지 "리튬" 오기인지 원본 CSV 재확인
