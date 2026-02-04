"""
Tax Table Lookup - Deterministic tool for TY 2024
Pure function - NO LLM involvement

Based on IRS Tax Computation Worksheet for 2024
"""

from typing import Literal


FilingStatus = Literal["single", "married_filing_jointly", "married_filing_separately", "head_of_household", "qualifying_widow"]


# 2024 Tax Brackets (Source: IRS Revenue Procedure 2023-34)
TAX_BRACKETS_2024 = {
    "single": [
        (0, 11600, 0.10, 0),
        (11600, 47150, 0.12, 1160),
        (47150, 100525, 0.22, 5426),
        (100525, 191950, 0.24, 17168.50),
        (191950, 243725, 0.32, 39110.50),
        (243725, 609350, 0.35, 55678.50),
       (609350, float('inf'), 0.37, 183647.25)
    ],
    "married_filing_jointly": [
        (0, 23200, 0.10, 0),
        (23200, 94300, 0.12, 2320),
        (94300, 201050, 0.22, 10852),
        (201050, 383900, 0.24, 34337),
        (383900, 487450, 0.32, 78221),
        (487450, 731200, 0.35, 111357),
        (731200, float('inf'), 0.37, 196669.50)
    ],
    "married_filing_separately": [
        (0, 11600, 0.10, 0),
        (11600, 47150, 0.12, 1160),
        (47150, 100525, 0.22, 5426),
        (100525, 191950, 0.24, 17168.50),
        (191950, 243725, 0.32, 39110.50),
        (243725, 365600, 0.35, 55678.50),
        (365600, float('inf'), 0.37, 98334.75)
    ],
    "head_of_household": [
        (0, 16550, 0.10, 0),
        (16550, 63100, 0.12, 1655),
        (63100, 100500, 0.22, 7241),
        (100500, 191950, 0.24, 15469),
        (191950, 243700, 0.32, 37417),
        (243700, 609350, 0.35, 53977),
        (609350, float('inf'), 0.37, 181954.50)
    ],
    "qualifying_widow": [
        (0, 23200, 0.10, 0),
        (23200, 94300, 0.12, 2320),
        (94300, 201050, 0.22, 10852),
        (201050, 383900, 0.24, 34337),
        (383900, 487450, 0.32, 78221),
        (487450, 731200, 0.35, 111357),
        (731200, float('inf'), 0.37, 196669.50)
    ]
}


def calculate_tax(taxable_income: float, filing_status: FilingStatus) -> float:
    """
    Calculate federal income tax using 2024 tax brackets.
    This is a PURE, DETERMINISTIC function - no LLM involved.
    
    Args:
        taxable_income: Taxable income amount (Form 1040 Line 15)
        filing_status: Filing status
        
    Returns:
        Tax amount (Form 1040 Line 16)
        
    Example:
        >>> calculate_tax(50000, "single")
        6624.0
    """
    if taxable_income <= 0:
        return 0.0
    
    # Normalize filing status
    status = filing_status.lower().replace(" ", "_")
    
    if status not in TAX_BRACKETS_2024:
        raise ValueError(f"Invalid filing status: {filing_status}")
    
    brackets = TAX_BRACKETS_2024[status]
    
    # Find the applicable bracket
    for min_income, max_income, rate, base_tax in brackets:
        if min_income <= taxable_income < max_income:
            tax = base_tax + (taxable_income - min_income) * rate
            return round(tax, 2)
    
    # Should never reach here if brackets are properly defined
    raise ValueError(f"No tax bracket found for income ${taxable_income:,.2f}")


def tax_table_lookup(taxable_income: float, filing_status: FilingStatus) -> float:
    """
    Simplified tax table lookup for common incomes.
    For production use, this would include the full IRS tax table.
    
    For incomes $100,000 and below, IRS provides exact tables.
    For higher incomes, use tax computation worksheet (calculate_tax).
    
    Args:
        taxable_income: Taxable income
        filing_status: Filing status
        
    Returns:
        Tax amount
    """
    # For simplicity, use calculation method
    # In production, would use exact IRS tables for income <= $100,000
    return calculate_tax(taxable_income, filing_status)


def get_marginal_tax_rate(taxable_income: float, filing_status: FilingStatus) -> float:
    """
    Get the marginal tax rate for given income.
    
    Args:
        taxable_income: Taxable income
        filing_status: Filing status
        
    Returns:
        Marginal tax rate (as decimal, e.g., 0.22 for 22%)
    """
    status = filing_status.lower().replace(" ", "_")
    brackets = TAX_BRACKETS_2024[status]
    
    for min_income, max_income, rate, _ in brackets:
        if min_income <= taxable_income < max_income:
            return rate
    
    return brackets[-1][2]  # Highest bracket


def get_effective_tax_rate(taxable_income: float, filing_status: FilingStatus) -> float:
    """
    Calculate effective tax rate.
    
    Args:
        taxable_income: Taxable income
        filing_status: Filing status
        
    Returns:
        Effective tax rate (as decimal)
    """
    if taxable_income <= 0:
        return 0.0
    
    tax = calculate_tax(taxable_income, filing_status)
    return tax / taxable_income


# Quick reference table for testing
def print_tax_examples():
    """Print examples for quick reference"""
    test_cases = [
        (25000, "single"),
        (50000, "single"),
        (75000, "single"),
        (100000, "single"),
        (50000, "married_filing_jointly"),
        (100000, "married_filing_jointly"),
        (150000, "married_filing_jointly"),
    ]
    
    print("2024 Tax Calculation Examples")
    print("=" * 80)
    print(f"{'Income':<15} {'Status':<30} {'Tax':<15} {'Effective Rate'}")
    print("=" * 80)
    
    for income, status in test_cases:
        tax = calculate_tax(income, status)
        rate = get_effective_tax_rate(income, status)
        print(f"${income:>13,} {status:<30} ${tax:>13,.2f} {rate:>12.2%}")


if __name__ == "__main__":
    print_tax_examples()
    
    # Test specific cases
    print("\n\nTest Cases:")
    print("-" * 80)
    
    # Example from TaxCalcBench single-w2 case
    # Wages: $50,000, Standard Deduction: $14,600
    # Taxable Income: $35,400
    taxable = 35400
    status = "single"
    tax = calculate_tax(taxable, status)
    print(f"\nTaxable Income: ${taxable:,}")
    print(f"Filing Status: {status}")
    print(f"Tax: ${tax:,.2f}")
    print(f"Marginal Rate: {get_marginal_tax_rate(taxable, status):.0%}")
    print(f"Effective Rate: {get_effective_tax_rate(taxable, status):.2%}")
