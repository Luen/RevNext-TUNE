"""Report parameter dataclasses for Parts Price List and Parts by Bin Location."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class PartsPriceListParams:
    from_department: str
    from_franchise: str
    to_franchise: str = None  # Default to same as from_franchise if None
    from_bin: str | None = None
    to_bin: str | None = None
    price_1: Literal["List"] = "List"
    price_2: Literal["Stock"] = "Stock"
    include_gst: bool = True
    output_file_type: Literal["CSV", "Excel"] = "CSV"
    output_file_name: str = None  # Will be set in the function


@dataclass
class PartsByBinLocationParams:
    from_department: str
    to_department: str | None = None  # Default to same as from_department if None
    from_franchise: str = "TOY"
    to_franchise: str | None = None  # Default to same as from_franchise if None
    from_bin: str | None = None
    to_bin: str | None = None
    from_movement_code: str | None = None
    to_movement_code: str | None = None
    show_stock_as: Literal["Physical Stock", "Available Stock"] = "Physical Stock"
    print_when_stock_not_zero: bool = True
    print_part_when_stock_is_zero: bool = False
    print_part_when_stock_on_order_is_zero: bool = False
    no_primary_bin_location: bool = False
    no_alternate_bin_location: bool = False
    no_primary_bin_but_has_alternate_bin: bool = False
    has_both_primary_and_alternate_bin_location: bool = False
    last_sale_before: str | None = None
    last_receipt_before: str | None = None
    print_average_cost: bool = False
    report_format: Literal[
        "Split departments onto new page", "Print all departments on one page"
    ] = "Split departments onto new page"
    output_file_type: Literal["CSV", "Excel"] = "CSV"
    output_file_name: str = None  # Will be set in the function
