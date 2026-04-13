# Comtrade 수집 함수 분리 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 노트북 Cell 1의 API 수집 루프를 `src/data/comtrade_client.py`로 분리하고, 노트북에서 한 줄 import로 호출하게 한다.

**Architecture:** `collect_russia_trade()` 함수 하나가 reporters × years 루프를 처리하고 `pd.DataFrame`을 반환. 노트북은 import 후 호출만 하며, Cell 2 이하 전처리는 그대로 유지.

**Tech Stack:** Python 3.12, pandas, comtradeapicall, pytest, unittest.mock

---

### Task 1: `src/data/` 패키지 생성

**Files:**
- Create: `src/data/__init__.py`
- Create: `tests/test_comtrade_client.py`

- [ ] **Step 1: `src/data/__init__.py` 생성**

```python
# src/data/__init__.py
```

빈 파일로 생성. `src/data/`가 Python 패키지로 인식되도록 함.

- [ ] **Step 2: 테스트 파일 빈 shell 생성**

```python
# tests/test_comtrade_client.py
"""comtrade_client 단위 테스트."""
import pandas as pd
import pytest
```

- [ ] **Step 3: 커밋**

```bash
git add src/data/__init__.py tests/test_comtrade_client.py
git commit -m "chore: src/data 패키지 및 테스트 파일 초기화"
```

---

### Task 2: `collect_russia_trade()` 함수 작성 (TDD)

**Files:**
- Create: `src/data/comtrade_client.py`
- Modify: `tests/test_comtrade_client.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_comtrade_client.py`에 추가:

```python
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest

from src.data.comtrade_client import collect_russia_trade


SAMPLE_DF = pd.DataFrame({
    "refYear": [2022, 2022],
    "refMonth": [3, 4],
    "cmdCode": ["7210", "8542"],
    "flowCode": ["X", "X"],
    "primaryValue": [1000000, 2000000],
    "reporterDesc": ["Armenia", "Armenia"],
})


class TestCollectRussiaTrade:
    def test_returns_dataframe(self):
        """정상 응답 시 DataFrame 반환."""
        reporters = {"Armenia": "51"}
        with patch("src.data.comtrade_client.comtradeapicall.getFinalData", return_value=SAMPLE_DF):
            result = collect_russia_trade(
                reporters=reporters,
                hs_codes="7210,8542",
                years=[2022],
            )
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_reporter_name_column_added(self):
        """reporterName 컬럼이 추가되어야 함."""
        reporters = {"Armenia": "51"}
        with patch("src.data.comtrade_client.comtradeapicall.getFinalData", return_value=SAMPLE_DF):
            result = collect_russia_trade(
                reporters=reporters,
                hs_codes="7210,8542",
                years=[2022],
            )
        assert "reporterName" in result.columns
        assert (result["reporterName"] == "Armenia").all()

    def test_empty_response_skipped(self):
        """API가 None 또는 빈 DataFrame 반환 시 건너뜀."""
        reporters = {"UAE": "784"}
        with patch("src.data.comtrade_client.comtradeapicall.getFinalData", return_value=None):
            result = collect_russia_trade(
                reporters=reporters,
                hs_codes="7210,8542",
                years=[2022],
            )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_multiple_reporters_concatenated(self):
        """여러 국가 데이터가 하나의 DataFrame으로 합쳐짐."""
        reporters = {"Armenia": "51", "Kazakhstan": "398"}
        armenia_df = SAMPLE_DF.copy()
        kazakhstan_df = SAMPLE_DF.assign(reporterDesc="Kazakhstan")

        def side_effect(*args, **kwargs):
            reporter_code = kwargs.get("reporterCode")
            return armenia_df if reporter_code == "51" else kazakhstan_df

        with patch("src.data.comtrade_client.comtradeapicall.getFinalData", side_effect=side_effect):
            result = collect_russia_trade(
                reporters=reporters,
                hs_codes="7210,8542",
                years=[2022],
            )
        assert set(result["reporterName"].unique()) == {"Armenia", "Kazakhstan"}
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/test_comtrade_client.py -v
```

예상 출력: `ImportError: cannot import name 'collect_russia_trade'`

- [ ] **Step 3: `src/data/comtrade_client.py` 구현**

```python
# src/data/comtrade_client.py
"""UN Comtrade API 데이터 수집 함수."""

import pandas as pd
import comtradeapicall

from src.config import get_comtrade_api_key


def collect_russia_trade(
    reporters: dict[str, str],
    hs_codes: str,
    years: list[int],
    flows: str = "M,X",
    partner_code: str = "643",
) -> pd.DataFrame:
    """UN Comtrade에서 대러 무역 데이터 수집.

    Parameters
    ----------
    reporters : dict[str, str]
        국가명 → Comtrade 국가코드 매핑. 예: {"Armenia": "51"}
    hs_codes : str
        쉼표로 구분된 HS 코드. 예: "7210,8542"
    years : list[int]
        수집할 연도 목록. 예: [2020, 2021, 2022, 2023, 2024]
    flows : str
        수출입 구분. "M,X" (기본값) = 수입+수출
    partner_code : str
        상대국 코드. 기본값 "643" = 러시아

    Returns
    -------
    pd.DataFrame
        수집된 원시 데이터. 실패한 국가/연도는 경고 출력 후 건너뜀.
        데이터가 없으면 빈 DataFrame 반환.
    """
    api_key = get_comtrade_api_key()
    all_list = []

    for r_name, r_code in reporters.items():
        for year in years:
            periods = [f"{year}{m:02d}" for m in range(1, 13)]
            period_str = ",".join(periods)

            print(f"Collecting {r_name} -> Russia, year {year} ...")

            df = comtradeapicall.getFinalData(
                api_key,
                typeCode="C",
                freqCode="M",
                clCode="HS",
                period=period_str,
                reporterCode=r_code,
                cmdCode=hs_codes,
                flowCode=flows,
                partnerCode=partner_code,
                partner2Code=None,
                customsCode=None,
                motCode=None,
                maxRecords=250000,
                format_output="JSON",
                aggregateBy=None,
                breakdownMode="plus",
                countOnly=None,
                includeDesc=True,
            )

            if df is None or len(df) == 0:
                print(f"  -> no data or error for {r_name}, {year}")
                continue

            df["reporterName"] = r_name
            all_list.append(df)

    if not all_list:
        return pd.DataFrame()

    return pd.concat(all_list, ignore_index=True)
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_comtrade_client.py -v
```

예상 출력:
```
test_comtrade_client.py::TestCollectRussiaTrade::test_returns_dataframe PASSED
test_comtrade_client.py::TestCollectRussiaTrade::test_reporter_name_column_added PASSED
test_comtrade_client.py::TestCollectRussiaTrade::test_empty_response_skipped PASSED
test_comtrade_client.py::TestCollectRussiaTrade::test_multiple_reporters_concatenated PASSED
```

- [ ] **Step 5: 커밋**

```bash
git add src/data/comtrade_client.py tests/test_comtrade_client.py
git commit -m "feat: UN Comtrade 수집 함수 collect_russia_trade 추가"
```

---

### Task 3: 노트북 Cell 1 교체

**Files:**
- Modify: `notebooks/제재_이후_특정_제_3국의_대리_수출이_구조적으로_증가했는가.ipynb` (Cell 0, Cell 1)

- [ ] **Step 1: Cell 0 — import 추가**

Cell 0 소스를 아래로 교체:

```python
import pandas as pd
import matplotlib.pyplot as plt
from src.data.comtrade_client import collect_russia_trade
from src.config import get_comtrade_api_key
```

- [ ] **Step 2: Cell 1 — 수집 루프를 함수 호출로 교체**

Cell 1 소스를 아래로 교체:

```python
# 데이터 수집 — reporters × years 루프는 src/data/comtrade_client.py 참조
reporters = {
    "Armenia": "51",
    "Kazakhstan": "398",
    "Georgia": "268",
    "Turkey": "792",
    "UAE": "784",
}

all_df = collect_russia_trade(
    reporters=reporters,
    hs_codes="7210,8542",
    years=list(range(2020, 2025)),
)

all_df.to_csv("comtrade_monthly_2020_2024_russia_7210_8542.csv", index=False)
all_df.head()
```

- [ ] **Step 3: Cell 2 이하 변경 없음 확인**

Cell 2(`ts = all_df[...]`)부터 이하 셀은 `all_df` 변수를 그대로 사용하므로 수정 불필요.

- [ ] **Step 4: 커밋**

```bash
git add "notebooks/제재_이후_특정_제_3국의_대리_수출이_구조적으로_증가했는가.ipynb"
git commit -m "refactor: 노트북 Cell 1 수집 루프를 collect_russia_trade() 호출로 교체"
```

---

### Task 4: 전체 테스트 통과 확인 및 마무리

- [ ] **Step 1: 전체 테스트 실행**

```bash
pytest tests/ -v
```

예상 출력: 모든 테스트 PASSED (기존 `test_features.py` 포함)

- [ ] **Step 2: 최종 푸시**

```bash
git push origin main
```
