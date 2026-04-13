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

---

## 최근 변경사항

<!-- CHANGELOG_START -->
## 최근 변경사항
**기타**
- 이슈 템플릿을 da-template 컨셉에 맞게 교체 ([`ac1de93`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/ac1de93fc42aeb0cc930c788c5d6d94a31586b9a))
- Src/data 패키지 및 테스트 파일 초기화 ([`dce932e`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/dce932e1f730f62bd96c0051fded5c858ad777af))
- Requirements.lock → uv.lock으로 교체 ([`81d0e78`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/81d0e7856e1380d1468d05f78c9d7473c13ed6ef))
- Requirements.txt 제거 (pyproject.toml + requirements.lock으로 통합) ([`b0cd57c`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/b0cd57c834c4d2a2cf2b6c578d4c21cbcfaea48c))
- Requirements.lock 추가 및 분석 노트북 초기 커밋 ([`5dd59cb`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/5dd59cb698d5b69ae1d2d5bb418dfb15ba8096ab))
- Uv 패키지 매니저로 전환 ([`8bf325f`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/8bf325f9eafddd183daefd7f629f70266b8898a9))

**리팩터링**
- 노트북 Cell 0, 1 수정 — collect_russia_trade() 함수 호출로 교체 ([`3deaefc`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/3deaefc9f11bc21e3cb913b42ff429239bf0424b))

**문서**
- CHANGELOG 자동 업데이트 [skip ci] ([`def5235`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/def5235c7c779317cbc4123e9677cb6270724f9d))
- CHANGELOG 자동 업데이트 [skip ci] ([`21574e6`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/21574e668ab4568078710161bfedc700216e4757))
- Comtrade 수집 함수 분리 구현 계획 추가 ([`614acff`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/614acffe3529dd6f17b847bab62d1fb6687a0dd1))
- CHANGELOG 자동 업데이트 [skip ci] ([`84bbd29`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/84bbd29a8cd8716ac6c963fab5c42aed68e61e63))
- Comtrade 수집 함수 분리 설계 문서 추가 ([`e620872`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/e6208725dca6440c21f4ddc424757ad05b09a619))
- CHANGELOG 자동 업데이트 [skip ci] ([`c4a19bf`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/c4a19bff79c568c7c3e751cba13b1dc299002c44))
- README 프로젝트 전용으로 재작성, cliff.toml 보고서 형식으로 업데이트 ([`ba8faa7`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/ba8faa7f47c47de92830707de2174e7210471e1a))
- CHANGELOG 자동 업데이트 [skip ci] ([`7a77391`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/7a77391034c0861cc3da09fe1564eddd0a767ac8))
- CHANGELOG 자동 업데이트 [skip ci] ([`a0bcbc9`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/a0bcbc9bf937b5ba210df685ecbd7ef6e0624e05))
- README 프로젝트 현황 반영 업데이트 ([`9f9031b`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/9f9031bc9d199c7b47111a32b9b685697ef62b11))
- CHANGELOG 자동 업데이트 [skip ci] ([`1a942ed`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/1a942edaab226e5212f553ecb78f3c78711f1713))
- CHANGELOG 자동 업데이트 [skip ci] ([`90df4b5`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/90df4b582d5dea7e757c14627b09c1fbbeb26e67))
- CHANGELOG 자동 업데이트 [skip ci] ([`d86aec4`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/d86aec47dc133275318fcd87f161a869005ae722))
- CHANGELOG 자동 업데이트 [skip ci] ([`97372d5`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/97372d51caead39f88eb4aedb89035aa37982169))
- CHANGELOG 자동 업데이트 [skip ci] ([`47a605f`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/47a605f9f0385a4586671595b53f326f2a47fb1c))
- CHANGELOG 자동 업데이트 [skip ci] ([`8d515b4`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/8d515b421a6f0263f3f84b45b5b5cf8fb8ba3c3c))
- CHANGELOG 자동 업데이트 [skip ci] ([`c67b20e`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/c67b20eafe2aa7e47910f375c89a6816583d034c))

**버그 수정**
- Comtrade_client 코드 품질 개선 (타입 체크, copy, 상수 분리) ([`e4ea9c0`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/e4ea9c0cf9849a2f4ea7075be29541edb5d3696d))
- Docs/superpowers 스펙 문서 git 추적 허용 ([`c4b5d6b`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/c4b5d6b4ed999279df877ae5e173ff911465d992))

**분석 노트북**
- 분석 내용 업데이트 ([`730b38b`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/730b38b7cbc31e97913307c3d6c1e3c3c8669790))

**새 기능**
- UN Comtrade 수집 함수 collect_russia_trade 추가 ([`83fc545`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/83fc545ebd3f2a84f8a7ae6b0ac4ffa99ade1792))
- README에 최근 변경사항 자동 주입 추가 ([`9f75bca`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/9f75bca111ca93aa0778eed023c81edf1b7d2c81))
- API 키 환경변수 로더 추가 및 노트북 하드코딩 제거 ([`d7b48e6`](https://github.com/JungYeoni/trade-circumvention-monitor/commit/d7b48e66694a4175a6f52e2091d6020e1dfbd9b4))
<!-- CHANGELOG_END -->

---

## 라이선스

MIT
