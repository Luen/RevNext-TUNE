"""
Download Parts By Bin Location CSV report from Revolution Next (*.revolutionnext.com.au).
Uses auto-login with session persistence (no manual cookie export).
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional, Union

from revnext.common import get_or_create_session, run_report_flow
from revnext.config import RevNextConfig

SERVICE_OBJECT = "Revolution.Activity.IM.RPT.PartsByBinLocationPR"
ACTIVITY_TAB_ID = "Nce9eac79_528b_4fc4_a294_b055a6dde16b"


@dataclass
class PartsByBinLocationParams:
    """Parameters for the Parts By Bin Location report. All of company, division, and department fields default to empty (no filter)."""

    company: str = ""
    division: str = ""
    department: str = ""
    from_department: str = ""
    to_department: str = ""
    from_franchise: str = ""
    to_franchise: str = ""
    from_bin: str = ""
    to_bin: str = ""
    from_movement_code: str = ""
    to_movement_code: str = ""
    # "Physical Stock" -> stktyp "P", "Available Stock" -> "A"
    show_stock_as: Literal["Physical Stock", "Available Stock"] = "Available Stock"
    print_when_stock_not_zero: bool = False
    print_part_when_stock_zero: bool = False
    print_part_when_stock_on_order_zero: bool = False
    no_primary_bin_location: bool = False
    no_alternate_bin_location: bool = False
    no_primary_but_has_alternate_bin: bool = False
    has_both_primary_and_alternate_bin: bool = False
    last_sale_before: Optional[str] = None  # ISO date-time or None
    last_receipt_before: Optional[str] = None
    print_average_cost: bool = False


def _build_submit_body(params: PartsByBinLocationParams) -> dict:
    """Build the submitActivityTask request body from params."""
    tz = "+10:00"
    now = datetime.now()
    start_date = now.strftime("%Y-%m-%d")
    start_time = f"{start_date}T{now.strftime('%H:%M')}:00.000{tz}"
    stktyp = "P" if params.show_stock_as == "Physical Stock" else "A"
    return {
        "_userContext_vg_coid": params.company,
        "_userContext_vg_divid": params.division,
        "_userContext_vg_dftdpt": params.department,
        "activityTabId": ACTIVITY_TAB_ID,
        "dataSets": [
            {
                "name": "dsActivityTask",
                "id": None,
                "dataSet": {
                    "dsActivityTask": {
                        "prods:hasChanges": True,
                        "ttActivityTask": [
                            {
                                "prods:id": "ttActivityTask1827072",
                                "prods:rowState": "created",
                                "fldId": 1,
                                "taskID": "",
                                "loadRowidPassThrough": "dummy",
                                "executeActivityTaskNow": False,
                                "executedAt": None,
                                "logMessages": "",
                                "startTime": None,
                                "endTime": None,
                            }
                        ],
                        "prods:before": {},
                    }
                },
            },
            {
                "name": "dsActivityTaskTriggers",
                "id": None,
                "dataSet": {
                    "dsActivityTaskTriggers": {
                        "prods:hasChanges": True,
                        "ttActivityTaskTrigger": [
                            {
                                "prods:id": "ttActivityTaskTrigger1972480",
                                "prods:rowState": "created",
                                "fldId": 1,
                                "mode": "O",
                                "startDateTime": start_time,
                                "startDate": f"{start_date}T00:00:00.000{tz}",
                                "startHour": now.hour,
                                "startMinute": now.minute,
                                "recurEvery": 1,
                                "recurEveryUOM": "days",
                                "weeklySun": False,
                                "weeklyMon": False,
                                "weeklyTue": False,
                                "weeklyWed": False,
                                "weeklyThu": False,
                                "weeklyFri": False,
                                "weeklySat": False,
                                "monthsList": "",
                                "monthlyMode": "",
                                "monthlyDaysList": "",
                                "monthlyOnWeekNumber": "",
                                "monthlyOnDayOfWeek": "",
                                "triggerDescription": "",
                                "triggerNextSchedule": None,
                                "windowTimeFrom": "",
                                "windowTimeTo": "",
                                "windowAllDay": False,
                            }
                        ],
                        "prods:before": {},
                    }
                },
            },
            {
                "name": "dsParams",
                "id": None,
                "dataSet": {
                    "dsParams": {
                        "prods:hasChanges": True,
                        "tt_params": [
                            {
                                "prods:id": "tt_paramsFldId1",
                                "prods:rowState": "modified",
                                "fldid": 1,
                                "coid": params.company,
                                "divid": params.division,
                                "activityid": "IM.RPT.PartsByBinLocationPR",
                                "taskid": "",
                                "tasksts": None,
                                "rptid": "",
                                "pdf": "",
                                "formprt": False,
                                "csvout": True,
                                "emailopt": "n",
                                "emailme": False,
                                "useremail": "",
                                "emailprinter": False,
                                "prtid": "",
                                "ddpflg": False,
                                "ddpquo": 0,
                                "submitopt": "p",
                                "email_staff": False,
                                "staff_email": "",
                                "email_other": False,
                                "other_email": "",
                                "subject": "Parts By Bin Location",
                                "attn": "",
                                "email_text": "",
                                "email_signature": "",
                                "email_sig_type": "D",
                                "frmdptid": params.from_department,
                                "todptid": params.to_department,
                                "frmfrnid": params.from_franchise,
                                "tofrnid": params.to_franchise,
                                "frmbinid": params.from_bin,
                                "tobinid": params.to_bin,
                                "frmmovecode": params.from_movement_code,
                                "tomovecode": params.to_movement_code,
                                "stktyp": stktyp,
                                "prntnotzero": params.print_when_stock_not_zero,
                                "prntzero": params.print_part_when_stock_zero,
                                "prntstkzero": params.print_part_when_stock_on_order_zero,
                                "noprimarybin": params.no_primary_bin_location,
                                "noalternatebin": params.no_alternate_bin_location,
                                "hasalternateonly": params.no_primary_but_has_alternate_bin,
                                "bothprimaryalternate": params.has_both_primary_and_alternate_bin,
                                "lastsaledate": params.last_sale_before,
                                "lastreceiptdate": params.last_receipt_before,
                                "prntavgcost": params.print_average_cost,
                                "rptformat": "N",
                                "tasktype": "",
                            }
                        ],
                        "prods:before": {
                            "tt_params": [
                                {
                                    "prods:id": "tt_paramsFldId1",
                                    "prods:rowState": "modified",
                                    "fldid": 1,
                                    "coid": params.company,
                                    "divid": params.division,
                                    "activityid": "",
                                    "taskid": "",
                                    "tasksts": None,
                                    "rptid": "",
                                    "pdf": "",
                                    "formprt": False,
                                    "csvout": False,
                                    "emailopt": "",
                                    "emailme": False,
                                    "useremail": "",
                                    "emailprinter": False,
                                    "prtid": "",
                                    "ddpflg": False,
                                    "ddpquo": 0,
                                    "submitopt": "",
                                    "email_staff": False,
                                    "staff_email": "",
                                    "email_other": False,
                                    "other_email": "",
                                    "subject": "",
                                    "attn": "",
                                    "email_text": "",
                                    "email_signature": "",
                                    "email_sig_type": "",
                                    "frmdptid": params.from_department,
                                    "todptid": params.to_department,
                                    "frmfrnid": "",
                                    "tofrnid": "",
                                    "frmbinid": "",
                                    "tobinid": "",
                                    "frmmovecode": "",
                                    "tomovecode": "",
                                    "stktyp": stktyp,
                                    "prntnotzero": False,
                                    "prntzero": False,
                                    "prntstkzero": False,
                                    "noprimarybin": False,
                                    "noalternatebin": False,
                                    "hasalternateonly": False,
                                    "bothprimaryalternate": False,
                                    "lastsaledate": None,
                                    "lastreceiptdate": None,
                                    "prntavgcost": False,
                                    "rptformat": "",
                                    "tasktype": "",
                                }
                            ]
                        },
                    }
                },
            },
        ],
        "stopOnWarning": True,
        "validateOnly": False,
        "uiType": "ISC",
    }


def download_parts_by_bin_report(
    config: Optional[RevNextConfig] = None,
    output_path: Optional[Path | str] = None,
    base_url: Optional[str] = None,
    report_params: Optional[PartsByBinLocationParams] = None,
    *,
    company: Optional[str] = None,
    division: Optional[str] = None,
    department: Optional[str] = None,
    from_department: Optional[str] = None,
    to_department: Optional[str] = None,
    from_franchise: Optional[str] = None,
    to_franchise: Optional[str] = None,
    from_bin: Optional[str] = None,
    to_bin: Optional[str] = None,
    from_movement_code: Optional[str] = None,
    to_movement_code: Optional[str] = None,
    show_stock_as: Optional[Literal["Physical Stock", "Available Stock"]] = None,
    print_when_stock_not_zero: Optional[bool] = None,
    print_part_when_stock_zero: Optional[bool] = None,
    print_part_when_stock_on_order_zero: Optional[bool] = None,
    no_primary_bin_location: Optional[bool] = None,
    no_alternate_bin_location: Optional[bool] = None,
    no_primary_but_has_alternate_bin: Optional[bool] = None,
    has_both_primary_and_alternate_bin: Optional[bool] = None,
    last_sale_before: Optional[str] = None,
    last_receipt_before: Optional[str] = None,
    print_average_cost: Optional[bool] = None,
    max_polls: int = 60,
    poll_interval: float = 2,
    return_data: bool = False,
    report_label: Optional[str] = None,
) -> Union[Path, bytes]:
    """
    Run the Parts By Bin Location report. By default saves CSV to output_path and returns the Path.
    If return_data=True, returns the report content as bytes (no file saved); use e.g. pd.read_csv(io.BytesIO(data)).

    Args:
        config: RevNext config. Defaults to RevNextConfig.from_env().
        output_path: Where to save the CSV when return_data=False. Defaults to current dir / Parts_By_Bin_Location.csv.
        base_url: Override base URL (otherwise from config).
        return_data: If True, do not save to file; return the CSV content as bytes.
        report_params: Optional params object; overridden by any keyword args below.
        company: Company code. Default "" (no filter).
        division: Division code. Default "" (no filter).
        department: Department code for context. Default "" (no department).
        from_department: From department code. Default "" (no filter).
        to_department: To department code. Default "" (no filter).
        from_franchise / to_franchise: Franchise codes (use codes, not display names).
        from_bin / to_bin: Bin codes.
        from_movement_code / to_movement_code: Movement codes (must be valid for department/franchise).
        show_stock_as: "Physical Stock" or "Available Stock". Default "Available Stock".
        print_when_stock_not_zero: Include parts when stock not zero.
        print_part_when_stock_zero: Include parts when stock zero.
        print_part_when_stock_on_order_zero: Include parts when stock on order zero.
        no_primary_bin_location: Only parts with no primary bin.
        no_alternate_bin_location: Only parts with no alternate bin.
        no_primary_but_has_alternate_bin: Only parts with no primary but have alternate.
        has_both_primary_and_alternate_bin: Only parts with both primary and alternate.
        last_sale_before: Last sale before date (ISO date-time or None).
        last_receipt_before: Last receipt before date (ISO date-time or None).
        print_average_cost: Include average cost in report.
        return_data: If True, return CSV bytes instead of saving to a file.
    """
    config = config or RevNextConfig.from_env()
    base_url = base_url or config.base_url
    if return_data:
        out_path = None
    else:
        out_path = (
            Path(output_path)
            if output_path is not None
            else (Path.cwd() / "Parts_By_Bin_Location.csv")
        )
    params = report_params or PartsByBinLocationParams()
    kwargs = {
        "company": company,
        "division": division,
        "department": department,
        "from_department": from_department,
        "to_department": to_department,
        "from_franchise": from_franchise,
        "to_franchise": to_franchise,
        "from_bin": from_bin,
        "to_bin": to_bin,
        "from_movement_code": from_movement_code,
        "to_movement_code": to_movement_code,
        "show_stock_as": show_stock_as,
        "print_when_stock_not_zero": print_when_stock_not_zero,
        "print_part_when_stock_zero": print_part_when_stock_zero,
        "print_part_when_stock_on_order_zero": print_part_when_stock_on_order_zero,
        "no_primary_bin_location": no_primary_bin_location,
        "no_alternate_bin_location": no_alternate_bin_location,
        "no_primary_but_has_alternate_bin": no_primary_but_has_alternate_bin,
        "has_both_primary_and_alternate_bin": has_both_primary_and_alternate_bin,
        "last_sale_before": last_sale_before,
        "last_receipt_before": last_receipt_before,
        "print_average_cost": print_average_cost,
    }
    if any(v is not None for v in kwargs.values()):
        params = PartsByBinLocationParams(
            **{k: v if v is not None else getattr(params, k) for k, v in kwargs.items()}
        )
    session = get_or_create_session(config, SERVICE_OBJECT)

    def get_body():
        return _build_submit_body(params)

    label = report_label or (
        f"Parts by Bin Location - {params.department}"
        if params.department
        else "Parts by Bin Location"
    )
    return run_report_flow(
        session,
        SERVICE_OBJECT,
        ACTIVITY_TAB_ID,
        get_body,
        base_url,
        output_path=out_path,
        max_polls=max_polls,
        poll_interval=poll_interval,
        report_label=label,
    )


if __name__ == "__main__":
    download_parts_by_bin_report()
