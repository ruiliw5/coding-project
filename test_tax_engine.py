"""
Updated 2025 tests for the tax calculation engine.
"""
from decimal import Decimal
from tax_engine import run_tax_calculation

def test_2025_single_middle_income():
    # Income: $65,000
    # Deduction: $15,750 (2025 Standard)
    # Taxable: $49,250
    # Calculation:
    # 10% on 11,925 = 1,192.50
    # 12% on (48,475 - 11,925) = 4,386.00
    # 22% on (49,250 - 48,475) = 170.50
    # Total Tax: 5,749.00
    r = run_tax_calculation(
        gross_income=Decimal("65000"),
        filing_status="single"
    )
    assert r["taxable_income"] == Decimal("49250.00")
    assert r["tax_owed"] == Decimal("5749.00")
    assert r["marginal_bracket"]["bracket_label"] == "22%"
    print("2025 Single Middle Income Test Passed")

def test_2025_married_high_income():
    # Income: $150,000
    # Deduction: $31,500
    # Taxable: $118,500
    r = run_tax_calculation(
        gross_income=Decimal("150000"),
        filing_status="married_joint"
    )
    # 10% on 23,850 = 2,385
    # 12% on (96,950 - 23,850) = 8,772
    # 22% on (118,500 - 96,950) = 4,741
    # Total: 15,898
    assert r["tax_owed"] == Decimal("15898.00")
    print("2025 Married Joint High Income Test Passed")

if __name__ == "__main__":
    test_2025_single_middle_income()
    test_2025_married_high_income()
    print("All 2025 Engine tests passed successfully.")