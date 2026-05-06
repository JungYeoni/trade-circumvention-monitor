# 설계 문서: UN Comtrade 데이터 수집 함수 분리

**날짜:** 2026-04-13  
**대상 파일:** `03_russia_sanctions_trade_shift_analysis.ipynb`

---

## 목표

노트북 Cell 1에 인라인으로 작성된 API 수집 루프를 `src/data/comtrade_client.py`로 분리한다.  
노트북은 함수를 import해서 호출하는 구조로 단순화한다.  
전처리(Cell 2 이하)는 노트북에 유지하며, 다른 노트북에서도 사용이 필요해질 경우 그 시점에 `src/`로 이동한다.

---

## 범위

- **포함:** 수집 루프 → 함수화, 노트북 Cell 1 교체
- **제외:** retry 로직, 캐싱, 전처리 분리

---

## 설계

### `src/data/comtrade_client.py`

```python
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
    reporters : dict
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
    """
```

**내부 동작:**
1. `reporters × years` 루프를 돌며 `comtradeapicall.getFinalData()` 호출
2. 응답이 None 또는 빈 DataFrame이면 경고 출력 후 건너뜀
3. 각 결과에 `reporterName` 컬럼 추가
4. 전체 결과를 `pd.concat`해서 반환

### `src/data/__init__.py`

빈 파일. 패키지 인식용.

### 노트북 Cell 1 교체

기존:
```python
# 50줄의 수집 루프
all_list = []
for r_name, r_code in reporters.items():
    for year in years:
        ...
all_df = pd.concat(all_list)
```

변경 후:
```python
from src.data.comtrade_client import collect_russia_trade

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
```

---

## 파일 변경 목록

| 파일 | 변경 유형 |
|------|----------|
| `src/data/__init__.py` | 신규 생성 |
| `src/data/comtrade_client.py` | 신규 생성 |
| `notebooks/03_russia_sanctions_trade_shift_analysis.ipynb` | Cell 1 교체 |

---

## 향후 확장 지점

- 다른 노트북에서 동일 수집 로직 필요 시 → `collect_russia_trade()` import로 바로 재사용 가능
- 국가/품목 확장 필요 시 → 파라미터만 변경
- retry/캐싱 필요 시 → 함수 내부에 추가 (노트북 인터페이스 변화 없음)
