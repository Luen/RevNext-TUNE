"""
Download all requested reports to a folder with default parameters except company/division/department.
Run from repo root: python download_all_reports.py
"""
from pathlib import Path

from revnext import download_parts_by_bin_report, download_parts_price_list_report

OUTPUT_DIR = Path(__file__).resolve().parent / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# (company, division, department, label for filename)
REPORTS = [
    ("03", "1", "130", "MCT_Parts_Accessories"),
    ("03", "1", "145", "MCT_Tyres"),
    ("03", "1", "330", "Ingham_Toyota"),
    ("04", "2", "430", "Charters_Towers_Partnership"),
]

def main():
    for company, division, department, label in REPORTS:
        # Parts Price List
        out_ppl = OUTPUT_DIR / f"Parts_Price_List_{label}_{company}_{division}_{department}.csv"
        print(f"Downloading Parts Price List: {label} ({company}/{division}/{department}) -> {out_ppl.name}")
        download_parts_price_list_report(
            company=company,
            division=division,
            department=department,
            output_path=out_ppl,
            max_polls=180,
            poll_interval=2,
        )
        # Parts By Bin Location
        out_bin = OUTPUT_DIR / f"Parts_By_Bin_Location_{label}_{company}_{division}_{department}.csv"
        print(f"Downloading Parts By Bin Location: {label} ({company}/{division}/{department}) -> {out_bin.name}")
        download_parts_by_bin_report(
            company=company,
            division=division,
            department=department,
            from_department=department,
            to_department=department,
            output_path=out_bin,
            max_polls=180,
            poll_interval=2,
        )
    print(f"Done. All reports saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
