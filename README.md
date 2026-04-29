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
| `UN Comtrade.ipynb` | Comtrade API 연동 및 데이터 수집 기초 |
| `제재_이후_특정_제_3국의_대리_수출이_구조적으로_증가했는가.ipynb` | 제재 전후 월별 수출 시계열 분석, 국가별 증가율 비교 |
| `관세청_수출입실적(GW).ipynb` | 관세청 API 연동 및 품목별 수출입 데이터 수집 |

---

## 환경 설정

```bash
# 가상환경 생성 및 의존성 설치
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev]"

# API 키 설정
cp .env.example .env  # .env에 키 값 입력
```

`.env` 파일에 필요한 키:

```
COMTRADE_API_KEY=...
CUSTOMS_TRADE_STATS_API_KEY=...
```

## 라이선스

MIT
