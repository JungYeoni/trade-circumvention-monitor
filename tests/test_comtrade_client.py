# tests/test_comtrade_client.py
"""comtrade_client 단위 테스트."""
from unittest.mock import patch

import pandas as pd

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
        """API가 None 반환 시 건너뜀 → 빈 DataFrame."""
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
