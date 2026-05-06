# 무역 우회 모니터링 (Trade Circumvention Monitor)

러시아 제재 이후 제3국을 경유한 무역 우회 패턴을 탐지하고 분석하는 데이터 분석 프로젝트입니다.  
UN Comtrade 및 관세청 API를 활용해 품목·국가별 수출입 데이터를 수집하고, 제재 전후 구조적 변화를 정량적으로 분석합니다.

---

## 분석 개요

- **분석 대상**: 러시아 제재(2022.02) 이후 제3국 경유 수출입 패턴 변화
- **주요 품목**: HS 7210 (평판압연철강), HS 8542 (반도체)
- **대상 국가**: 아르메니아, 카자흐스탄, 조지아, 튀르키예, UAE
- **데이터 출처**: UN Comtrade API, 관세청 품목별 국가별 수출입실적 API

---

## 노트북

| 파일 | 내용 |
|------|------|
| `01_un_comtrade_api_example.ipynb` | Comtrade API 연동 및 데이터 수집 기초 |
| `02_customs_trade_api_example.ipynb` | 관세청 API 연동 및 품목별 수출입 데이터 수집 |
| `03_russia_sanctions_trade_shift_analysis.ipynb` | 제재 전후 월별 대러 수출 시계열 분석, 국가별 증가율 비교 |
| `04_regulation_event_preprocessing.ipynb` | 덤핑방지 관세 원천 데이터를 규제 이벤트·HS 매핑 템플릿·분석 후보 테이블로 전처리 |

---

## 환경 설정

```bash
# 의존성 설치
uv sync --extra dev

# API 키 설정
cp .env.example .env  # .env에 키 값 입력
```

`.env` 파일에 필요한 키:

```
COMTRADE_API_KEY=...
CUSTOMS_TRADE_STATS_API_KEY=...
```

자세한 의존성 관리 방식은 `DEPENDENCY_MANAGEMENT.md`를 참고하세요.

## 라이선스

MIT
