"""
Download Parts Price List CSV report from Revolution Next (*.revolutionnext.com.au).
Uses auto-login with session persistence (no manual cookie export).
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional, Union

import requests

from revnext.common import get_or_create_session, run_report_flow
from revnext.config import RevNextConfig

SERVICE_OBJECT = "Revolution.Activity.IM.RPT.PartsPriceListPR"
ACTIVITY_TAB_ID = "N78b54de4_7cdc_43e0_9e42_71a49bec44f2"


@dataclass
class PartsPriceListParams:
    """Parameters for the Parts Price List report. All default to current behavior if omitted."""

    company: str = "03"
    division: str = "1"
    department: str = "130"
    # Stock Parts ("stock") or Supplier Parts ("supplier") -> prttyp "s" or "p"
    part_type: Literal["stock", "supplier"] = "stock"
    from_franchise: str = ""
    to_franchise: str = ""
    from_bin: str = ""
    to_bin: str = ""
    # Price 1: API code e.g. "L" (List), "I", "TG"
    price_1: str = "L"
    include_gst_1: bool = True
    # Price 2: API code e.g. "S" (Stock), "R", "ST"
    price_2: str = "S"
    include_gst_2: bool = True


def _build_submit_body(params: PartsPriceListParams) -> dict:
    """Build the submitActivityTask request body from params. Use today's date for the trigger."""
    tz = "+10:00"
    now = datetime.now()
    start_date = now.strftime("%Y-%m-%d")
    start_time = f"{start_date}T{now.strftime('%H:%M')}:00.000{tz}"
    prttyp = "s" if params.part_type == "stock" else "p"
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
                                "prods:id": "ttActivityTask1945856",
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
                                "prods:id": "ttActivityTaskTrigger1786112",
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
                                "activityid": "IM.RPT.PartsPriceListPR",
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
                                "subject": "Parts Price List",
                                "attn": "",
                                "email_text": "",
                                "email_signature": "",
                                "email_sig_type": "D",
                                "prttyp": prttyp,
                                "dptid": params.department,
                                "frnid": params.from_franchise,
                                "frnidto": params.to_franchise,
                                "binid": params.from_bin,
                                "binidto": params.to_bin,
                                "prctyp1": params.price_1,
                                "prctyp2": params.price_2,
                                "incgst1": params.include_gst_1,
                                "incgst2": params.include_gst_2,
                                "exportexcel": False,
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
                                    "prttyp": prttyp,
                                    "dptid": params.department,
                                    "frnid": "",
                                    "frnidto": "",
                                    "binid": "",
                                    "binidto": "",
                                    "prctyp1": "",
                                    "prctyp2": "",
                                    "incgst1": False,
                                    "incgst2": False,
                                    "exportexcel": False,
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


def _post_submit_closesubmit_factory(base_url: str, company: str, division: str, department: str):
    """Return a hook that calls onChoose_btn_closesubmit (required for Parts Price List flow)."""
    def _post_submit_closesubmit(session: requests.Session) -> None:
        url = f"{base_url}/next/rest/si/presenter/onChoose_btn_closesubmit"
        body = {
            "_userContext_vg_coid": company,
            "_userContext_vg_divid": division,
            "_userContext_vg_dftdpt": department,
            "activityTabId": ACTIVITY_TAB_ID,
            "ctrlProp": [
                {"name": "tt_params.submitopt", "prop": "SCREENVALUE", "value": "p"}
            ],
            "uiType": "ISC",
        }
        r = session.post(url, json=body)
        r.raise_for_status()
    return _post_submit_closesubmit


def download_parts_price_list_report(
    config: Optional[RevNextConfig] = None,
    output_path: Optional[Path | str] = None,
    base_url: Optional[str] = None,
    report_params: Optional[PartsPriceListParams] = None,
    *,
    company: Optional[str] = None,
    division: Optional[str] = None,
    department: Optional[str] = None,
    part_type: Optional[Literal["stock", "supplier"]] = None,
    from_franchise: Optional[str] = None,
    to_franchise: Optional[str] = None,
    from_bin: Optional[str] = None,
    to_bin: Optional[str] = None,
    price_1: Optional[str] = None,
    include_gst_1: Optional[bool] = None,
    price_2: Optional[str] = None,
    include_gst_2: Optional[bool] = None,
    max_polls: int = 60,
    poll_interval: float = 2,
    return_data: bool = False,
) -> Union[Path, bytes]:
    """
    Run the Parts Price List report. By default saves CSV to output_path and returns the Path.
    If return_data=True, returns the report content as bytes (no file saved); use e.g. pd.read_csv(io.BytesIO(data)).

    Args:
        config: RevNext config. Defaults to RevNextConfig.from_env().
        output_path: Where to save the CSV when return_data=False. Defaults to current dir / Parts_Price_List.csv.
        base_url: Override base URL (otherwise from config).
        return_data: If True, do not save to file; return the CSV content as bytes.
        report_params: Optional params object; overridden by any keyword args below.
        company: Company code (e.g. "03"). Default "03".
        division: Division code (e.g. "1"). Default "1".
        department: Department code (e.g. "130"). Default "130".
        part_type: "stock" or "supplier". Default "stock".
        from_franchise: From franchise code (e.g. "OL"). Use codes, not display names.
        to_franchise: To franchise code.
        from_bin: From bin code.
        to_bin: To bin code.
        price_1: Price 1 API code (e.g. "L" List, "I", "TG"). Default "L".
        include_gst_1: Include GST for price 1. Default True.
        price_2: Price 2 API code (e.g. "S" Stock, "R", "ST"). Default "S".
        include_gst_2: Include GST for price 2. Default True.
        return_data: If True, return CSV bytes instead of saving to a file.
    """
    config = config or RevNextConfig.from_env()
    base_url = base_url or config.base_url
    if return_data:
        out_path = None
    else:
        out_path = Path(output_path) if output_path is not None else (Path.cwd() / "Parts_Price_List.csv")
    params = report_params or PartsPriceListParams()
    if any(
        x is not None
        for x in (
            company,
            division,
            department,
            part_type,
            from_franchise,
            to_franchise,
            from_bin,
            to_bin,
            price_1,
            include_gst_1,
            price_2,
            include_gst_2,
        )
    ):
        params = PartsPriceListParams(
            company=company if company is not None else params.company,
            division=division if division is not None else params.division,
            department=department if department is not None else params.department,
            part_type=part_type if part_type is not None else params.part_type,
            from_franchise=from_franchise if from_franchise is not None else params.from_franchise,
            to_franchise=to_franchise if to_franchise is not None else params.to_franchise,
            from_bin=from_bin if from_bin is not None else params.from_bin,
            to_bin=to_bin if to_bin is not None else params.to_bin,
            price_1=price_1 if price_1 is not None else params.price_1,
            include_gst_1=include_gst_1 if include_gst_1 is not None else params.include_gst_1,
            price_2=price_2 if price_2 is not None else params.price_2,
            include_gst_2=include_gst_2 if include_gst_2 is not None else params.include_gst_2,
        )
    if not (params.price_1 or "").strip() and not (params.price_2 or "").strip():
        raise ValueError(
            "You must select at least one price type to print a price listing. "
            "Set price_1 and/or price_2 (e.g. price_1='L', price_2='S', or price_1='F', price_2='O')."
        )
    session = get_or_create_session(config, SERVICE_OBJECT)
    get_body = lambda: _build_submit_body(params)
    return run_report_flow(
        session,
        SERVICE_OBJECT,
        ACTIVITY_TAB_ID,
        get_body,
        base_url,
        output_path=out_path,
        post_submit_hook=_post_submit_closesubmit_factory(
            base_url, params.company, params.division, params.department
        ),
        max_polls=max_polls,
        poll_interval=poll_interval,
    )


if __name__ == "__main__":
    download_parts_price_list_report()
