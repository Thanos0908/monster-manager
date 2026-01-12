from __future__ import annotations
from decimal import Decimal
from typing import Dict, Union

CRInput = Union[Decimal, float, int, str]

# Fixed mapping from D&D 5e rules (MM/Basic Rules).
CR_XP: Dict[Decimal, int] = {
    Decimal("0"): 10,        # default for CR 0 (often shown as 0–10 XP; use xp_override to represent 0)
    Decimal("0.125"): 25,    # 1/8
    Decimal("0.25"): 50,     # 1/4
    Decimal("0.5"): 100,     # 1/2
    Decimal("1"): 200, Decimal("2"): 450, Decimal("3"): 700, Decimal("4"): 1100,
    Decimal("5"): 1800, Decimal("6"): 2300, Decimal("7"): 2900, Decimal("8"): 3900,
    Decimal("9"): 5000, Decimal("10"): 5900, Decimal("11"): 7200, Decimal("12"): 8400,
    Decimal("13"): 10000, Decimal("14"): 11500, Decimal("15"): 13000, Decimal("16"): 15000,
    Decimal("17"): 18000, Decimal("18"): 20000, Decimal("19"): 22000, Decimal("20"): 25000,
    Decimal("21"): 33000, Decimal("22"): 41000, Decimal("23"): 50000, Decimal("24"): 62000,
    Decimal("25"): 75000, Decimal("26"): 90000, Decimal("27"): 105000, Decimal("28"): 120000,
    Decimal("29"): 135000, Decimal("30"): 155000,
}


def xp_for_cr(cr: CRInput) -> int:
    """
    Return XP for a given CR.

    Note: CR 0 maps to 10 by default. If you need 0 XP for CR 0, use xp_override.
    Raises ValueError if CR is unsupported.
    """
    c = Decimal(str(cr))
    try:
        return CR_XP[c]
    except KeyError as e:
        raise ValueError(f"Unsupported challenge rating: {cr}") from e


def cr_label(cr: CRInput) -> str:
    """Human label for CR (e.g., 0.125 -> '1/8', 0.5 -> '1/2')."""
    c = Decimal(str(cr))

    if c == Decimal("0.125"):
        return "1/8"
    if c == Decimal("0.25"):
        return "1/4"
    if c == Decimal("0.5"):
        return "1/2"

    # Integer CRs shown without decimals.
    if c == c.to_integral_value():
        return str(int(c))

    return str(c)