# da-template

[![Use this template](https://img.shields.io/badge/Use%20this%20template-2ea44f?style=for-the-badge&logo=github)](https://github.com/JungYeoni/da-template/generate)

개인 또는 소규모 팀을 위한 데이터분석·ML 프로젝트 템플릿입니다.  
새 프로젝트를 시작할 때 위 버튼을 눌러 레포를 생성하면, 일관된 디렉터리 구조·재현성 기준·협업 규칙·GitHub 자동화를 바로 사용할 수 있습니다.

---

## 적합한 프로젝트 유형

- 정형 데이터 EDA 및 분류/회귀
- 시계열 분석 및 예측
- 회귀/인과추론 (OLS, DiD, 패널 데이터)
- GIS 결합형 데이터 분석
- 논문·보고서용 시각화 + 인터랙티브 대시보드

---

## 디렉터리 구조

```
da-template/
├── CLAUDE.md                     # 프로젝트 분석 원칙 (Claude Code 지침)
├── pyproject.toml                # Python 의존성 및 도구 설정
├── uv.lock                       # 의존성 버전 고정 (uv 자동 관리)
├── .env                          # API 키 설정 (git 추적 제외)
├── .gitignore
│
├── .claude/
│   ├── CLAUDE.md                 # 전역 역할·스택 설정
│   ├── settings.json             # 민감 파일 접근 제한
│   ├── agents/                   # 서브에이전트 역할 정의
│   │   ├── data-scientist.md
│   │   ├── data-visualization.md
│   │   └── feature-engineer.md
│   ├── commands/                 # 슬래시 커맨드 (/timeseries 등)
│   └── rules/                    # 분석 규칙 (코드 스타일, 워크플로우 등)
│
├── .github/
│   ├── CODEOWNERS
│   ├── pull_request_template.md
│   ├── ISSUE_TEMPLATE/
│   │   ├── experiment.yml        # 실험 계획 이슈 템플릿
│   │   ├── bug_report.yml
│   │   └── config.yml
│   └── workflows/
│       ├── ci.yml                # lint + test
│       ├── notebook-smoke-test.yml
│       └── pr-title-lint.yml
│
├── configs/
│   ├── base.yaml                 # 공통 설정 (seed, split 비율, 경로 등)
│   ├── dev.yaml                  # 개발 환경 오버라이드
│   └── prod.yaml                 # 최종 제출 환경 오버라이드
│
├── data/
│   ├── raw/          # 원본 데이터 (git 추적 제외)
│   ├── interim/      # 중간 처리 결과
│   └── processed/    # 모델 입력용 최종 데이터
│
├── notebooks/        # 탐색·실험용 Jupyter 노트북
├── reports/          # 최종 보고서·시각화 산출물
│
├── src/
│   ├── config.py                    # API 키 로더 (환경변수에서 로드)
│   ├── features/
│   │   └── build_features.py    # 시계열·테이블·GIS 피처 함수
│   ├── modeling/
│   │   └── train.py             # 모델 학습 유틸리티
│   ├── evaluation/
│   │   └── evaluate.py          # 평가 지표 계산
│   └── visualization/
│       └── plots.py             # 정적 시각화 함수
│
└── tests/
    └── test_features.py         # 피처 단위 테스트
```

---

## 시작 방법

```bash
# 1. 저장소 클론
git clone https://github.com/JungYeoni/da-template.git my-project
cd my-project

# 2. 가상환경 생성 및 의존성 설치 (uv 사용)
uv venv --python 3.12
source .venv/bin/activate          # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# 3. API 키 설정
cp .env.example .env               # .env 파일 생성 후 키 값 입력

# 4. 테스트 실행 (환경 확인)
pytest tests/ -v
```

---

## 새 실험을 시작하는 기본 흐름

1. **GitHub Issue 생성** — `[Experiment]` 템플릿으로 목표·데이터·분할 전략 문서화
2. **브랜치 생성** — `git checkout -b experiment/short-description`
3. **`configs/base.yaml` 확인** — random seed, split 비율, 경로 설정
4. **노트북 작성** — `notebooks/` 아래에서 EDA 및 실험
5. **재사용 함수 정리** — `src/` 하위 모듈로 이동 후 테스트 작성
6. **PR 생성** — `[Experiment]` 접두사, PR 체크리스트 작성

### PR 제목 규칙

| 접두사 | 사용 시점 |
|--------|----------|
| `[Experiment]` | 새 분석 실험 |
| `[Feature]` | 피처 추가·수정 |
| `[Fix]` | 버그 수정 |
| `[Docs]` | 문서 변경 |
| `[Refactor]` | 기능 변경 없는 코드 정리 |
| `[Chore]` | 의존성, 설정 변경 |

---

## 핵심 원칙

### 재현성
- `np.random.seed(42)` 고정
- 데이터 분할 기준을 코드 주석으로 명시
- 전처리는 `sklearn.Pipeline` 내에서만 수행

### 데이터 누수 방지
- 피처 생성 전에 train/val/test 분리 확정
- 시계열 rolling/lag은 `shift(1)` 후 계산
- 인코더·스케일러 파라미터는 학습 데이터에서만 fit

### 방법론적 타당성 우선
- 성능보다 통계적 가정 검증, 계수 해석, 한계점 명시를 우선
- 복잡한 모델보다 해석 가능하고 재현 가능한 방법 선택

---

## Claude Code 연동

`CLAUDE.md` (프로젝트 루트)와 `.claude/` 폴더가 Claude Code에서 자동으로 로드됩니다.

### 슬래시 커맨드

| 커맨드 | 기능 |
|--------|------|
| `/timeseries` | 시계열 분석 — ADF, ARIMA, Prophet |
| `/tabular` | 테이블 EDA — 기술통계, 이상치, 상관관계 |
| `/gis` | 지리공간 분석 — geopandas, folium |
| `/regression` | 회귀 분석 — OLS, VIF, 잔차 진단 |
| `/ml` | ML 파이프라인 — 전처리, 모델 비교, SHAP |
| `/visualization` | 시각화 — matplotlib, seaborn, plotly |

### 서브에이전트

`.claude/agents/` 파일을 Claude Code가 에이전트로 로드합니다.

| 에이전트 | 역할 |
|----------|------|
| `data-scientist` | 통계 분석, 시계열, 회귀/인과추론, sklearn ML |
| `feature-engineer` | 피처 설계·검증 (시계열, 테이블, GIS) |
| `data-visualization` | 정적 이미지(dpi=300) + Plotly/Streamlit 대시보드 |

> Claude Code 외 다른 코딩 에이전트(Cursor, Copilot 등)를 사용하는 경우에도 `CLAUDE.md`와 `src/` 코드가 분석 원칙 참고 문서로 활용될 수 있습니다.

---

## GitHub Actions

| 워크플로우 | 트리거 | 내용 |
|-----------|--------|------|
| `ci.yml` | push/PR → main | ruff lint, black format check, pytest |
| `notebook-smoke-test.yml` | PR에서 notebooks/ 변경 | 변경된 노트북 실행 가능 여부 확인 |
| `pr-title-lint.yml` | PR 생성/수정 | 제목 접두사 형식 확인 |
| `changelog.yml` | push → main | `CHANGELOG.md` 자동 생성 (git-cliff) |

---

## 최근 변경사항

<!-- CHANGELOG_START -->
<!-- CHANGELOG_END -->

---

## 라이선스

MIT
