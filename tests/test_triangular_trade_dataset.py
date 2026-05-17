from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.data.triangular_trade_dataset import (
    FLOW_INTERMEDIARY_TO_KOREA,
    FLOW_REGULATED_TO_INTERMEDIARY,
    FLOW_REGULATED_TO_KOREA,
    SOURCE_COMTRADE,
    SOURCE_CUSTOMS,
    build_triangular_trade_panel,
    collect_triangular_trade_with_resume,
    make_triangular_trade_collection_plan,
    normalize_comtrade_response,
)


def test_make_triangular_trade_collection_plan_creates_three_flows_per_intermediary():
    events = pd.DataFrame(
        [
            {
                "event_id": "AD-0001-01",
                "origin_country_name_kr": "일본",
                "product_name_kr": "D.C.P",
                "hs_code": "290219",
                "duty_text_raw": "가격약속",
                "duty_type": "price_undertaking",
                "duty_rate_min": None,
                "duty_rate_max": None,
                "start_date": "2020-03-15",
                "end_date": "2020-09-20",
            }
        ]
    )
    intermediaries = pd.DataFrame(
        [{"event_id": "AD-0001-01", "intermediary_country": "베트남"}]
    )
    country_codes = pd.DataFrame(
        [
            {
                "country_name_kr": "일본",
                "comtrade_reporter_code": "392",
                "comtrade_partner_code": "392",
                "customs_country_code": "JP",
            },
            {
                "country_name_kr": "베트남",
                "comtrade_reporter_code": "704",
                "comtrade_partner_code": "704",
                "customs_country_code": "VN",
            },
        ]
    )

    plan = make_triangular_trade_collection_plan(
        events, intermediaries, country_codes, today="2021-12-31"
    )

    assert len(plan) == 3
    assert set(plan["flow_type"]) == {
        FLOW_REGULATED_TO_INTERMEDIARY,
        FLOW_INTERMEDIARY_TO_KOREA,
        FLOW_REGULATED_TO_KOREA,
    }
    assert (
        plan.loc[plan["flow_type"].eq(FLOW_REGULATED_TO_INTERMEDIARY), "source"].item()
        == SOURCE_COMTRADE
    )
    assert set(
        plan.loc[~plan["flow_type"].eq(FLOW_REGULATED_TO_INTERMEDIARY), "source"]
    ) == {SOURCE_CUSTOMS}
    assert plan["start_yymm"].eq("201903").all()
    assert plan["end_yymm"].eq("202109").all()


def test_normalize_comtrade_response_fills_missing_months():
    request = pd.Series(
        {
            "request_id": "REQ-1",
            "event_id": "AD-0001-01",
            "flow_type": FLOW_REGULATED_TO_INTERMEDIARY,
            "source": SOURCE_COMTRADE,
            "regulated_country": "일본",
            "intermediary_country": "베트남",
            "importer_country": "대한민국",
            "reporter_country": "일본",
            "partner_country": "베트남",
            "hs_code": "290219",
            "periods": "202001,202002",
        }
    )
    response = pd.DataFrame(
        [{"refYear": 2020, "refMonth": 1, "qty": "10", "primaryValue": "200"}]
    )

    rows = normalize_comtrade_response(request, response)

    assert len(rows) == 2
    assert rows[0]["year_month"] == "202001"
    assert rows[0]["quantity"] == 10
    assert rows[0]["value_usd"] == 200
    assert rows[1]["year_month"] == "202002"
    assert rows[1]["quantity"] == 0


def test_build_triangular_trade_panel_pivots_three_flows():
    plan = pd.DataFrame(
        [
            {
                "event_id": "AD-0001-01",
                "regulated_country": "일본",
                "intermediary_country": "베트남",
                "importer_country": "대한민국",
                "hs_code": "290219",
                "product_name": "D.C.P",
                "duty_text_raw": "가격약속",
                "duty_type": "price_undertaking",
                "duty_rate_min": "",
                "duty_rate_max": "",
                "start_date": "2020-03-15",
                "end_date": "2020-09-20",
            }
        ]
    )
    long_df = pd.DataFrame(
        [
            _long_row(FLOW_REGULATED_TO_INTERMEDIARY, SOURCE_COMTRADE, 10, 100),
            _long_row(FLOW_INTERMEDIARY_TO_KOREA, SOURCE_CUSTOMS, 20, 200),
            _long_row(FLOW_REGULATED_TO_KOREA, SOURCE_CUSTOMS, 30, 300),
        ]
    )

    panel = build_triangular_trade_panel(long_df, plan)

    assert len(panel) == 1
    row = panel.iloc[0]
    assert row["규제국_중간국_수출량"] == 10
    assert row["중간국_한국_수출량"] == 20
    assert row["규제국_한국_수출량"] == 30
    assert row["규제국_중간국_source"] == SOURCE_COMTRADE
    assert row["중간국_한국_source"] == SOURCE_CUSTOMS
    assert row["규제국_한국_source"] == SOURCE_CUSTOMS


def test_collect_triangular_trade_with_resume_skips_ok_requests(tmp_path: Path):
    plan = pd.DataFrame(
        [
            _plan_row("REQ-1", FLOW_REGULATED_TO_INTERMEDIARY, SOURCE_COMTRADE),
            _plan_row("REQ-2", FLOW_REGULATED_TO_INTERMEDIARY, SOURCE_COMTRADE),
        ]
    )
    plan_path = tmp_path / "plan.csv"
    status_path = tmp_path / "status.csv"
    long_path = tmp_path / "long.csv"
    panel_path = tmp_path / "panel.csv"
    plan.to_csv(plan_path, index=False)
    pd.DataFrame(
        [
            {
                "request_id": "REQ-1",
                "status": "ok",
                "rows": "1",
                "error": "",
                "started_at": "",
                "finished_at": "",
            }
        ]
    ).to_csv(status_path, index=False)
    pd.DataFrame(
        [_long_row(FLOW_REGULATED_TO_INTERMEDIARY, SOURCE_COMTRADE, 1, 1)]
    ).to_csv(long_path, index=False)

    with (
        patch(
            "src.data.triangular_trade_dataset.get_comtrade_api_key", return_value="key"
        ),
        patch(
            "src.data.triangular_trade_dataset.get_customs_api_key", return_value="key"
        ),
        patch(
            "src.data.triangular_trade_dataset.collect_one_triangular_request"
        ) as patched,
    ):
        patched.return_value = [
            _long_row(FLOW_REGULATED_TO_INTERMEDIARY, SOURCE_COMTRADE, 2, 2)
        ]
        collect_triangular_trade_with_resume(
            plan_path, status_path, long_path, panel_path
        )

    assert patched.call_count == 1
    status = pd.read_csv(status_path)
    assert status["status"].eq("ok").sum() == 2


def _long_row(flow_type: str, source: str, quantity: int, value: int) -> dict:
    return {
        "request_id": "REQ-1",
        "event_id": "AD-0001-01",
        "flow_type": flow_type,
        "source": source,
        "regulated_country": "일본",
        "intermediary_country": "베트남",
        "importer_country": "대한민국",
        "reporter_country": "일본",
        "partner_country": "베트남",
        "hs_code": "290219",
        "year_month": "202001",
        "quantity": quantity,
        "value_usd": value,
    }


def _plan_row(request_id: str, flow_type: str, source: str) -> dict:
    return {
        "request_id": request_id,
        "event_id": "AD-0001-01",
        "flow_type": flow_type,
        "source": source,
        "regulated_country": "일본",
        "intermediary_country": "베트남",
        "importer_country": "대한민국",
        "reporter_country": "일본",
        "partner_country": "베트남",
        "reporter_code": "392",
        "partner_code": "704",
        "customs_country_code": "",
        "hs_code": "290219",
        "periods": "202001",
        "start_yymm": "202001",
        "end_yymm": "202001",
        "product_name": "D.C.P",
        "duty_text_raw": "가격약속",
        "duty_type": "price_undertaking",
        "duty_rate_min": "",
        "duty_rate_max": "",
        "start_date": "2020-03-15",
        "end_date": "2020-09-20",
    }
