"""
Standard Deduction Calculator - Deterministic tool for TY 2024
Pure function - NO LLM involvement

Source: IRS Revenue Procedure 2023-34
"""

from typing import Literal, Optional


FilingStatus = Literal["single", "married_filing_jointly", "married_filing_separately", "head_of_household", "qualifying_widow"]


# 2024 Standard Deduction Amounts
STANDARD_DEDUCTION_2024 = {
    "single": 14600,
    "married_filing_jointly": 29200,
    "married_filing_separately": 14600,
    "head_of_household": 21900,
    "qualifying_widow": 29200
}

# Additional standard deduction for age 65+ or blind
ADDITIONAL_DEDUCTION_2024 = {
    "single": 1950,
    "married_filing_jointly": 1550,  # Per person
    "married_filing_separately": 1550,
    "head_of_household": 1950,
    "qualifying_widow": 1550
}


def get_standard_deduction(
    filing_status: FilingStatus,
    taxpayer_age: Optional[int] = None,
    taxpayer_blind: bool = False,
    spouse_age: Optional[int] = None,
    spouse_blind: bool = False
) -> float:
    """
    Calculate standard deduction for 2024.
    This is a PURE, DETERMINISTIC function - no LLM involved.
    
    Args:
        filing_status: Filing status
        taxpayer_age: Taxpayer's age (for 65+ additional deduction)
        taxpayer_blind: Whether taxpayer is blind
        spouse_age: Spouse's age (for MFJ/QW)
        spouse_blind: Whether spouse is blind (for MFJ/QW)
        
    Returns:
        Standard deduction amount
        
    Example:
        >>> get_standard_deduction("single")
        14600.0
        >>> get_standard_deduction("single", taxpayer_age=66)
        16550.0
    """
    # Normalize filing status
    status = filing_status.lower().replace(" ", "_")
    
    if status not in STANDARD_DEDUCTION_2024:
        raise ValueError(f"Invalid filing status: {filing_status}")
    
    # Base standard deduction
    deduction = STANDARD_DEDUCTION_2024[status]
    
    # Additional deduction for taxpayer (age 65+ or blind)
    additional = ADDITIONAL_DEDUCTION_2024[status]
    
    # Taxpayer additions
    if taxpayer_age and taxpayer_age >= 65:
        deduction += additional
    if taxpayer_blind:
        deduction += additional
    
    # Spouse additions (only for MFJ and QW)
    if status in ["married_filing_jointly", "qualifying_widow"]:
        if spouse_age and spouse_age >= 65:
            deduction += additional
        if spouse_blind:
            deduction += additional
    
    return float(deduction)


def should_itemize(
    filing_status: FilingStatus,
    total_itemized_deductions: float,
    taxpayer_age: Optional[int] = None,
    taxpayer_blind: bool = False,
    spouse_age: Optional[int] = None,
    spouse_blind: bool = False
) -> bool:
    """
    Determine if taxpayer should itemize deductions.
    
    Args:
        filing_status: Filing status
        total_itemized_deductions: Total of itemized deductions (Schedule A)
        taxpayer_age: Taxpayer's age
        taxpayer_blind: Whether taxpayer is blind
        spouse_age: Spouse's age
        spouse_blind: Whether spouse is blind
        
    Returns:
        True if should itemize, False if should use standard deduction
    """
    standard = get_standard_deduction(
        filing_status,
        taxpayer_age,
        taxpayer_blind,
        spouse_age,
        spouse_blind
    )
    
    return total_itemized_deductions > standard


def get_deduction_amount(
    filing_status: FilingStatus,
    itemized_deductions: Optional[float] = None,
    taxpayer_age: Optional[int] = None,
    taxpayer_blind: bool = False,
    spouse_age: Optional[int] = None,
    spouse_blind: bool = False
) -> tuple[float, str]:
    """
    Get the deduction amount and type (standard or itemized).
    
    Args:
        filing_status: Filing status
        itemized_deductions: Total itemized deductions (if any)
        taxpayer_age: Taxpayer's age
        taxpayer_blind: Whether taxpayer is blind
        spouse_age: Spouse's age
        spouse_blind: Whether spouse is blind
        
    Returns:
        Tuple of (deduction_amount, deduction_type)
    """
    standard = get_standard_deduction(
        filing_status,
        taxpayer_age,
        taxpayer_blind,
        spouse_age,
        spouse_blind
    )
    
    if itemized_deductions is None or itemized_deductions <= standard:
        return standard, "standard"
    else:
        return itemized_deductions, "itemized"


def print_deduction_table():
    """Print reference table of standard deductions"""
    print("2024 Standard Deduction Amounts")
    print("=" * 80)
    print(f"{'Filing Status':<35} {'Base':<15} {'65+/Blind':<15}")
    print("=" * 80)
    
    for status in STANDARD_DEDUCTION_2024:
        base = STANDARD_DEDUCTION_2024[status]
        additional = ADDITIONAL_DEDUCTION_2024[status]
        print(f"{status.replace('_', ' ').title():<35} ${base:>13,} +${additional:>12,}")
    
    print("\nExamples with Additional Deductions:")
    print("=" * 80)
    
    examples = [
        ("Single, age 30", "single", None, False, None, False),
        ("Single, age 66", "single", 66, False, None, False),
        ("Single, age 66, blind", "single", 66, True, None, False),
        ("MFJ, both under 65", "married_filing_jointly", 45, False, 42, False),
        ("MFJ, one 65+", "married_filing_jointly", 66, False, 60, False),
        ("MFJ, both 65+", "married_filing_jointly", 66, False, 67, False),
        ("MFJ, both 65+, one blind", "married_filing_jointly", 66, True, 67, False),
    ]
    
    for desc, status, t_age, t_blind, s_age, s_blind in examples:
        deduction = get_standard_deduction(status, t_age, t_blind, s_age, s_blind)
        print(f"{desc:<45} ${deduction:>12,}")


if __name__ == "__main__":
    print_deduction_table()
    
    # Test specific cases
    print("\n\nTest Cases:")
    print("-" * 80)
    
    # Single filer
    deduction = get_standard_deduction("single")
    print(f"\nSingle filer: ${deduction:,}")
    
    # MFJ
    deduction = get_standard_deduction("married_filing_jointly")
    print(f"Married filing jointly: ${deduction:,}")
    
    # Should itemize test
    filing_status = "single"
    itemized = 18000
    standard = get_standard_deduction(filing_status)
    should_itemize_result = should_itemize(filing_status, itemized)
    
    print(f"\nItemization Decision:")
    print(f"  Filing Status: {filing_status}")
    print(f"  Standard Deduction: ${standard:,}")
    print(f"  Itemized Deductions: ${itemized:,}")
    print(f"  Should Itemize: {should_itemize_result}")
    
    deduction, deduction_type = get_deduction_amount(filing_status, itemized)
    print(f"  Using: {deduction_type.title()} deduction of ${deduction:,}")
