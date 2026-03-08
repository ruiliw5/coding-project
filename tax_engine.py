"""
Tax Calculation Engine - Simplified US Federal Income Tax Logic (Prototype)

Uses official 2025-style brackets and standard deduction for demonstration only.
NOT for actual tax filing.
"""

from decimal import Decimal
from typing import Literal

FilingStatus = Literal["single", "married_joint", "head_of_household"]

# 2025 Standard Deduction Amounts
STANDARD_DEDUCTIONS = {
    "single": Decimal("15750"),
    "married_joint": Decimal("31500"),
    "head_of_household": Decimal("23625"),
}

# 2025 Progressive Tax Brackets
BRACKETS_SINGLE = [
    (Decimal("0"), Decimal("0.10")),
    (Decimal("11925"), Decimal("0.12")),
    (Decimal("48475"), Decimal("0.22")),
    (Decimal("103350"), Decimal("0.24")),
    (Decimal("197300"), Decimal("0.32")),
    (Decimal("250525"), Decimal("0.35")),
    (Decimal("626350"), Decimal("0.37")),
]

BRACKETS_MARRIED = [
    (Decimal("0"), Decimal("0.10")),
    (Decimal("23850"), Decimal("0.12")),
    (Decimal("96950"), Decimal("0.22")),
    (Decimal("206700"), Decimal("0.24")),
    (Decimal("394600"), Decimal("0.32")),
    (Decimal("501050"), Decimal("0.35")),
    (Decimal("751600"), Decimal("0.37")),
]

BRACKETS_HOH = [
    (Decimal("0"), Decimal("0.10")),
    (Decimal("17000"), Decimal("0.12")),
    (Decimal("64850"), Decimal("0.22")),
    (Decimal("103350"), Decimal("0.24")),
    (Decimal("197300"), Decimal("0.32")),
    (Decimal("250500"), Decimal("0.35")),
    (Decimal("626350"), Decimal("0.37")),
]

BRACKETS_BY_STATUS = {
    "single": BRACKETS_SINGLE,
    "married_joint": BRACKETS_MARRIED,
    "head_of_household": BRACKETS_HOH,
}

def get_standard_deduction(filing_status: str) -> Decimal:
    return STANDARD_DEDUCTIONS.get(filing_status, STANDARD_DEDUCTIONS["single"])

def calculate_tax_on_taxable_income(taxable_income: Decimal, filing_status: str) -> Decimal:
    """Calculate federal income tax using 2025 progressive brackets."""
    if taxable_income <= 0:
        return Decimal("0")
    
    brackets = BRACKETS_BY_STATUS.get(filing_status, BRACKETS_SINGLE)
    tax = Decimal("0")
    
    for i in range(len(brackets)):
        threshold = brackets[i][0]
        rate = brackets[i][1]
        
        # Determine the upper limit of the current bracket
        if i + 1 < len(brackets):
            next_threshold = brackets[i + 1][0]
        else:
            next_threshold = taxable_income + 1
            
        bracket_ceiling = min(taxable_income, next_threshold)
        
        if bracket_ceiling > threshold:
            amount_in_bracket = bracket_ceiling - threshold
            tax += amount_in_bracket * rate
            
    return tax.quantize(Decimal("0.01"))


def get_marginal_bracket(taxable_income: Decimal, filing_status: str) -> dict:
    """
    Return the marginal (top) tax bracket for the given taxable income.
    Brackets start at 10%. Returns rate_pct, bracket_label, bracket_range.
    """
    brackets = BRACKETS_BY_STATUS.get(filing_status, BRACKETS_SINGLE)
    # First bracket 10% range: $0 to brackets[1][0] (start of 12% bracket)
    bracket_hi_10pct = int(brackets[1][0]) if len(brackets) > 1 else 11925
    status_label = {"single": "single", "married_joint": "married filing jointly", "head_of_household": "head of household"}.get(filing_status, "single")

    if taxable_income <= 0:
        return {
            "rate": Decimal("0"),
            "rate_pct": 0,
            "bracket_label": "N/A",
            "bracket_range": f"No taxable income. Brackets start at 10% ($0 – ${bracket_hi_10pct:,} for {status_label}).",
        }

    marginal_rate = brackets[0][1]
    bracket_lo = brackets[0][0]
    bracket_hi = brackets[1][0] if len(brackets) > 1 else taxable_income + 1
    is_top_bracket = False

    for i in range(len(brackets)):
        threshold = brackets[i][0]
        rate = brackets[i][1]
        next_threshold = brackets[i + 1][0] if i + 1 < len(brackets) else taxable_income + 1
        if taxable_income > threshold:
            marginal_rate = rate
            bracket_lo = threshold
            bracket_hi = next_threshold
            is_top_bracket = (i + 1 >= len(brackets))

    pct = int(marginal_rate * 100)
    range_str = f"over ${int(bracket_lo):,}" if is_top_bracket else f"${int(bracket_lo):,} – ${int(bracket_hi):,}"
    return {
        "rate": marginal_rate,
        "rate_pct": pct,
        "bracket_label": f"{pct}%",
        "bracket_range": range_str,
    }


def run_tax_calculation(
    gross_income: Decimal,
    filing_status: str,
    additional_deductions: Decimal = Decimal("0"),
    federal_withheld: Decimal = Decimal("0"),
    use_standard_deduction: bool = True,
) -> dict:
    """Full tax calculation. Returns dict with 2025 values for display."""
    standard_deduction = get_standard_deduction(filing_status) if use_standard_deduction else Decimal("0")
    total_deductions = standard_deduction + additional_deductions
    taxable_income = max(Decimal("0"), gross_income - total_deductions)
    
    tax_before_credits = calculate_tax_on_taxable_income(taxable_income, filing_status)
    tax_owed = tax_before_credits
    refund_or_owed = federal_withheld - tax_owed
    marginal_bracket = get_marginal_bracket(taxable_income, filing_status)

    return {
        "gross_income": gross_income.quantize(Decimal("0.01")),
        "standard_deduction": standard_deduction.quantize(Decimal("0.01")),
        "additional_deductions": additional_deductions.quantize(Decimal("0.01")),
        "total_deductions": total_deductions.quantize(Decimal("0.01")),
        "taxable_income": taxable_income.quantize(Decimal("0.01")),
        "tax_before_credits": tax_before_credits.quantize(Decimal("0.01")),
        "tax_owed": tax_owed.quantize(Decimal("0.01")),
        "federal_withheld": federal_withheld.quantize(Decimal("0.01")),
        "refund_or_owed": refund_or_owed.quantize(Decimal("0.01")),
        "is_refund": refund_or_owed >= 0,
        "marginal_bracket": marginal_bracket,
    }