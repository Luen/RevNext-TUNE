# tune_dms.parts.sales: Parts -> Sales menu (Work With Orders, etc.)

from tune_dms.parts.sales.work_with_orders import (
    WorkWithOrderParams,
    fill_add_order_form,
)

__all__ = [
    "WorkWithOrderParams",
    "fill_add_order_form",
]
