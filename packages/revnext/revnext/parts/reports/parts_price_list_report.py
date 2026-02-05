"""
Download Parts Price List CSV report from Revolution Next (*.revolutionnext.com.au).
Uses auto-login with session persistence (no manual cookie export).
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

from revnext.common import get_or_create_session, run_report_flow
from revnext.config import RevNextConfig, get_revnext_base_url_from_env

SERVICE_OBJECT = "Revolution.Activity.IM.RPT.PartsPriceListPR"
ACTIVITY_TAB_ID = "N78b54de4_7cdc_43e0_9e42_71a49bec44f2"


def _build_submit_body() -> dict:
    """Build the submitActivityTask request body. Use today's date for the trigger."""
    tz = "+10:00"
    now = datetime.now()
    start_date = now.strftime("%Y-%m-%d")
    start_time = f"{start_date}T{now.strftime('%H:%M')}:00.000{tz}"
    return {
        "_userContext_vg_coid": "03",
        "_userContext_vg_divid": "1",
        "_userContext_vg_dftdpt": "570",
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
                                "coid": "03",
                                "divid": "1",
                                "activityid": "IM.RPT.PartsPriceListPR",
                                "taskid": "",
                                "tasksts": None,
                                "rptid": "",
                                "pdf": "",
                                "formprt": False,
                                "csvout": True,
                                "emailopt": "n",
                                "emailme": False,
                                "useremail": "lwarneke@mikecarneytoyota.com.au",
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
                                "prttyp": "s",
                                "dptid": "570",
                                "frnid": "",
                                "frnidto": "",
                                "binid": "",
                                "binidto": "",
                                "prctyp1": "L",
                                "prctyp2": "S",
                                "incgst1": True,
                                "incgst2": True,
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
                                    "coid": "03",
                                    "divid": "1",
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
                                    "prttyp": "s",
                                    "dptid": "130",
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


def _post_submit_closesubmit_factory(base_url: str):
    """Return a hook that calls onChoose_btn_closesubmit (required for Parts Price List flow)."""
    def _post_submit_closesubmit(session: requests.Session) -> None:
        url = f"{base_url}/next/rest/si/presenter/onChoose_btn_closesubmit"
        body = {
            "_userContext_vg_coid": "03",
            "_userContext_vg_divid": "1",
            "_userContext_vg_dftdpt": "570",
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
) -> Path:
    """
    Run the Parts Price List report and save CSV to output_path.
    Returns the path where the file was saved.

    Args:
        config: RevNext config (tenant/URL, username, password, session path). Defaults to RevNextConfig.from_env().
        output_path: Where to save the CSV. Defaults to current dir / Parts_Price_List.csv.
        base_url: Override base URL (otherwise from config).
    """
    config = config or RevNextConfig.from_env()
    base_url = base_url or config.base_url
    output_path = Path(output_path) if output_path is not None else (Path.cwd() / "Parts_Price_List.csv")
    session = get_or_create_session(config, SERVICE_OBJECT)
    return run_report_flow(
        session,
        SERVICE_OBJECT,
        ACTIVITY_TAB_ID,
        _build_submit_body,
        output_path,
        base_url,
        post_submit_hook=_post_submit_closesubmit_factory(base_url),
    )


if __name__ == "__main__":
    download_parts_price_list_report()
