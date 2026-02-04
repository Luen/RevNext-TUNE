"""
Download both Revolution Next CSV reports (Parts By Bin Location and Parts Price List)
using cookies and optional config.
"""

from pathlib import Path
from typing import Optional

from revnext.parts_by_bin_report import download_parts_by_bin_report
from revnext.parts_price_list_report import download_parts_price_list_report


def download_all_reports(
    cookies_path: Optional[Path | str] = None,
    output_dir: Optional[Path | str] = None,
    base_url: Optional[str] = None,
) -> list[Path]:
    """
    Run both Parts By Bin Location and Parts Price List reports and save CSVs.
    Returns the list of paths where files were saved.

    Args:
        cookies_path: Path to cookies JSON. Defaults to current dir / revnext-cookies.json.
        output_dir: Directory for output CSVs. Defaults to current directory.
        base_url: Revolution Next base URL. Defaults to REVOLUTIONNEXT_URL env or default.
    """
    output_dir = Path(output_dir) if output_dir is not None else Path.cwd()

    saved: list[Path] = []
    print("--- Parts By Bin Location ---")
    path1 = download_parts_by_bin_report(
        cookies_path=cookies_path,
        output_path=output_dir / "Parts_By_Bin_Location.csv",
        base_url=base_url,
    )
    saved.append(path1)
    print("\n--- Parts Price List ---")
    path2 = download_parts_price_list_report(
        cookies_path=cookies_path,
        output_path=output_dir / "Parts_Price_List.csv",
        base_url=base_url,
    )
    saved.append(path2)
    print(f"\nDone. Saved {len(saved)} file(s).")
    return saved


if __name__ == "__main__":
    download_all_reports()
