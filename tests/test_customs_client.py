"""Customs client unit tests."""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.data.customs_client import collect_customs_trade, split_yymm_period


def test_split_yymm_period_splits_long_ranges():
    assert split_yymm_period("202401", "202502") == [
        ("202401", "202412"),
        ("202501", "202502"),
    ]


def test_split_yymm_period_rejects_reverse_range():
    with pytest.raises(ValueError):
        split_yymm_period("202502", "202401")


def test_collect_customs_trade_parses_xml_rows():
    xml = """
    <response>
      <header><resultCode>00</resultCode><resultMsg>NORMAL SERVICE.</resultMsg></header>
      <body><items>
        <item>
          <year>202401</year><statCdCntnKor1>미국</statCdCntnKor1><statCd>US</statCd>
          <statKor>밀</statKor><hsCd>1001999090</hsCd>
          <impDlr>100</impDlr><expDlr>0</expDlr><impWgt>20</impWgt><expWgt>0</expWgt>
          <balPayments>-100</balPayments>
        </item>
        <item><year>총계</year><impDlr>100</impDlr></item>
      </items></body>
    </response>
    """
    response = Mock(status_code=200, text=xml)

    with (
        patch("src.data.customs_client.get_customs_api_key", return_value="test-key"),
        patch("src.data.customs_client.requests.get", return_value=response),
    ):
        result = collect_customs_trade(
            start="202401",
            end="202401",
            hs_code="1001999090",
            countries={"United States": "US"},
        )

    assert isinstance(result, pd.DataFrame)
    assert result.shape[0] == 1
    assert result.loc[0, "query_country_name"] == "United States"
    assert result.loc[0, "impDlr"] == 100
