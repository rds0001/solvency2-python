"""Public mcr functions from the accepted source."""
from ._core import (
    de_branch_minimum_amount as de_branch_minimum_amount,
    mcr_absolute_floor as mcr_absolute_floor,
    mcr_combined as mcr_combined,
    mcr_life as mcr_life,
    mcr_nonlife as mcr_nonlife,
    mcr_capital_at_risk as mcr_capital_at_risk,
    mcr_linear as mcr_linear,
    mcr_notional_scr as mcr_notional_scr,
    mcr_notional_requirement as mcr_notional_requirement,
)

__all__ = ['de_branch_minimum_amount', 'mcr_absolute_floor', 'mcr_combined', 'mcr_life', 'mcr_nonlife', 'mcr_capital_at_risk', 'mcr_linear', 'mcr_notional_scr', 'mcr_notional_requirement']
