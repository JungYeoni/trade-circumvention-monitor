"""Run ESR Comtrade collection with checkpoint files."""

from __future__ import annotations

import sys
from pathlib import Path

import comtradeapicall
import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parents[1]
sys.path.insert(0, str(CURRENT_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

from esr import _comtrade_response_to_esr_rows, _wide_esr_dataset_from_long_rows
from src.config import get_comtrade_api_key


def main() -> None:
    input_dir = PROJECT_ROOT / "sr_indicator" / "0. datasets" / "input"
    plan_path = input_dir / "esr_comtrade_collection_plan.csv"
    long_path = input_dir / "esr_export_flow_long_raw.csv"
    wide_path = input_dir / "esr_export_flow_dataset.csv"
    status_path = input_dir / "esr_comtrade_collection_status.csv"

    plan = pd.read_csv(plan_path, dtype=str).fillna("")
    api_key = get_comtrade_api_key()

    if long_path.exists():
        long_rows = pd.read_csv(long_path, dtype={"pair_id": str}).to_dict("records")
    else:
        long_rows = []

    if status_path.exists():
        status = pd.read_csv(status_path, dtype=str).fillna("")
        done_keys = set(status.loc[status["status"].eq("ok"), "request_key"])
    else:
        status = pd.DataFrame(columns=["request_key", "status", "rows", "error"])
        done_keys = set()

    status_records = status.to_dict("records")
    consecutive_empty_responses = 0
    pending_empty_results: list[tuple[str, list[dict], int]] = []

    for idx, request in plan.iterrows():
        key = _request_key(request)
        if key in done_keys:
            continue

        print(
            "Collecting "
            f"{idx + 1}/{len(plan)} "
            f"pair={request['pair_id']} "
            f"{request['규제국']}->{request['partner_country']} "
            f"hs={request['hs_code']} "
            f"{request['flow_type']}",
            flush=True,
        )

        try:
            response_df = comtradeapicall.getFinalData(
                api_key,
                typeCode="C",
                freqCode="M",
                clCode="HS",
                period=str(request["periods"]),
                reporterCode=str(request["reporter_code"]),
                cmdCode=str(request["hs_code"]),
                flowCode=str(request["flow_code"]),
                partnerCode=str(request["partner_code"]),
                partner2Code=None,
                customsCode=None,
                motCode=None,
                maxRecords=250_000,
                format_output="JSON",
                aggregateBy=None,
                breakdownMode="plus",
                countOnly=None,
                includeDesc=True,
            )
            is_empty_response = response_df is None or (
                isinstance(response_df, pd.DataFrame) and response_df.empty
            )
            if is_empty_response:
                consecutive_empty_responses += 1
            else:
                consecutive_empty_responses = 0

            rows = _comtrade_response_to_esr_rows(request, response_df)

            if is_empty_response:
                pending_empty_results.append((key, rows, 0))

            if consecutive_empty_responses >= 5:
                status_records.append(
                    {
                        "request_key": key,
                        "status": "stopped_empty_streak",
                        "rows": "0",
                        "error": "Stopped after 5 consecutive empty API responses. Check quota or API status.",
                    }
                )
                _write_checkpoint(status_path, long_path, wide_path, status_records, long_rows, idx + 1)
                print(
                    "Stopped after 5 consecutive empty API responses. "
                    "This often means the Comtrade quota is exhausted.",
                    flush=True,
                )
                return

            if is_empty_response:
                continue

            for pending_key, pending_rows, pending_row_count in pending_empty_results:
                long_rows.extend(pending_rows)
                status_records.append(
                    {
                        "request_key": pending_key,
                        "status": "ok",
                        "rows": str(pending_row_count),
                        "error": "",
                    }
                )
                done_keys.add(pending_key)
            pending_empty_results.clear()

            long_rows.extend(rows)
            status_records.append(
                {
                    "request_key": key,
                    "status": "ok",
                    "rows": str(0 if response_df is None else len(response_df)),
                    "error": "",
                }
            )
            done_keys.add(key)
        except Exception as exc:  # noqa: BLE001 - keep batch collection moving.
            status_records.append(
                {"request_key": key, "status": "error", "rows": "0", "error": repr(exc)[:500]}
            )
            print(f"ERROR {repr(exc)}", flush=True)

        if (idx + 1) % 20 == 0 or idx == len(plan) - 1:
            _write_checkpoint(status_path, long_path, wide_path, status_records, long_rows, idx + 1)

    for pending_key, pending_rows, pending_row_count in pending_empty_results:
        long_rows.extend(pending_rows)
        status_records.append(
            {
                "request_key": pending_key,
                "status": "ok",
                "rows": str(pending_row_count),
                "error": "",
            }
        )

    _write_checkpoint(status_path, long_path, wide_path, status_records, long_rows, len(plan))
    print("DONE", flush=True)


def _request_key(request: pd.Series) -> str:
    return "|".join(
        [
            str(request["pair_id"]),
            str(request["flow_type"]),
            str(request["reporter_code"]),
            str(request["partner_code"]),
            str(request["hs_code"]),
            str(request["periods"]),
        ]
    )


def _write_checkpoint(
    status_path: Path,
    long_path: Path,
    wide_path: Path,
    status_records: list[dict],
    long_rows: list[dict],
    request_count: int,
) -> None:
    try:
        pd.DataFrame(status_records).to_csv(status_path, index=False, encoding="utf-8-sig")
        saved_status_path = status_path
    except PermissionError:
        saved_status_path = status_path.with_name(f"{status_path.stem}_latest{status_path.suffix}")
        pd.DataFrame(status_records).to_csv(saved_status_path, index=False, encoding="utf-8-sig")
    if long_rows:
        long_df = pd.DataFrame(long_rows)
        try:
            long_df.to_csv(long_path, index=False, encoding="utf-8-sig")
            saved_long_path = long_path
        except PermissionError:
            saved_long_path = long_path.with_name(f"{long_path.stem}_latest{long_path.suffix}")
            long_df.to_csv(saved_long_path, index=False, encoding="utf-8-sig")
        wide_df = _wide_esr_dataset_from_long_rows(long_df)
        try:
            wide_df.to_csv(wide_path, index=False, encoding="utf-8-sig")
            saved_wide_path = wide_path
        except PermissionError:
            saved_wide_path = wide_path.with_name(f"{wide_path.stem}_latest{wide_path.suffix}")
            wide_df.to_csv(saved_wide_path, index=False, encoding="utf-8-sig")
        print(
            f"checkpoint request={request_count} long_rows={len(long_df)} "
            f"wide_rows={len(wide_df)} status_path={saved_status_path.name} "
            f"long_path={saved_long_path.name} "
            f"wide_path={saved_wide_path.name}",
            flush=True,
        )
    else:
        print(
            f"checkpoint request={request_count} no rows yet "
            f"status_path={saved_status_path.name}",
            flush=True,
        )


if __name__ == "__main__":
    main()
