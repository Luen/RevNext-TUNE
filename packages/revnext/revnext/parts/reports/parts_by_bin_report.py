"""
Download Parts By Bin Location CSV report from Revolution Next (*.revolutionnext.com.au).
Uses auto-login with session persistence (no manual cookie export).
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from revnext.common import get_or_create_session, run_report_flow
from revnext.config import RevNextConfig, get_revnext_base_url_from_env

SERVICE_OBJECT = "Revolution.Activity.IM.RPT.PartsByBinLocationPR"
ACTIVITY_TAB_ID = "Nce9eac79_528b_4fc4_a294_b055a6dde16b"


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
                                "coid": "03",
                                "divid": "1",
                                "activityid": "IM.RPT.PartsByBinLocationPR",
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
                                "subject": "Parts By Bin Location",
                                "attn": "",
                                "email_text": "",
                                "email_signature": "",
                                "email_sig_type": "D",
                                "frmdptid": "570",
                                "todptid": "570",
                                "frmfrnid": "",
                                "tofrnid": "",
                                "frmbinid": "",
                                "tobinid": "",
                                "frmmovecode": "",
                                "tomovecode": "",
                                "stktyp": "A",
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
                                    "frmdptid": "130",
                                    "todptid": "130",
                                    "frmfrnid": "",
                                    "tofrnid": "",
                                    "frmbinid": "",
                                    "tobinid": "",
                                    "frmmovecode": "",
                                    "tomovecode": "",
                                    "stktyp": "P",
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
) -> Path:
    """
    Run the Parts By Bin Location report and save CSV to output_path.
    Returns the path where the file was saved.

    Args:
        config: RevNext config (tenant/URL, username, password, session path). Defaults to RevNextConfig.from_env().
        output_path: Where to save the CSV. Defaults to current dir / Parts_By_Bin_Location.csv.
        base_url: Override base URL (otherwise from config).
    """
    config = config or RevNextConfig.from_env()
    base_url = base_url or config.base_url
    output_path = Path(output_path) if output_path is not None else (Path.cwd() / "Parts_By_Bin_Location.csv")
    session = get_or_create_session(config, SERVICE_OBJECT)
    return run_report_flow(
        session,
        SERVICE_OBJECT,
        ACTIVITY_TAB_ID,
        _build_submit_body,
        output_path,
        base_url,
    )


if __name__ == "__main__":
    download_parts_by_bin_report()
