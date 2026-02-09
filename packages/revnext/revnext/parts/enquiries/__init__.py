"""
Enquiries (lookups) for Revolution Next parts – supplier part search and load.
"""

from revnext.parts.enquiries.supplier_part import (
    load_supplier_part,
    search_supplier_parts,
)

__all__ = [
    "load_supplier_part",
    "search_supplier_parts",
]
