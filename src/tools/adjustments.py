"""
Adjustments Toolkit - Deterministic calculations for Schedule 1
Includes:
- Educator Expense calculation
- Student Loan Interest deduction (with phase-outs)
- Excess Business Loss (Form 461) handling
"""

from typing import Union
from src.core.types import FilingStatus


def calculate_educator_expense(
    amount_paid: float, 
    is_eligible: bool,
    spouse_amount_paid: float = 0.0,
    spouse_eligible: bool = False,
    filing_status: Union[FilingStatus, str] = FilingStatus.SINGLE
) -> float:
    """
    Calculate deductible educator expenses for 2024.
    Max $300 per eligible person.
    """
    limit_per_person = 300.0
    deduction = 0.0
    
    if is_eligible:
        deduction += min(amount_paid, limit_per_person)
        
    if str(filing_status) == FilingStatus.MARRIED_FILING_JOINTLY and spouse_eligible:
        deduction += min(spouse_amount_paid, limit_per_person)
        
    return deduction


def calculate_student_loan_interest(
    interest_paid: float,
    magi: float,
    filing_status: Union[FilingStatus, str] = FilingStatus.SINGLE
) -> float:
    """
    Calculate Student Loan Interest Deduction for 2024.
    Max deduction: $2,500.
    
    Phase-out thresholds:
    - Single/HOH/Widow: $80,000 - $95,000
    - MFJ: $165,000 - $195,000
    """
    max_deduction = 2500.0
    deduction = min(interest_paid, max_deduction)
    
    status = str(filing_status)
    
    if status == FilingStatus.MARRIED_FILING_JOINTLY:
        start_phase = 165000.0
        end_phase = 195000.0
    else:
        start_phase = 80000.0
        end_phase = 95000.0
        
    if magi <= start_phase:
        return deduction
    elif magi >= end_phase:
        return 0.0
    else:
        # Phase-out calculation
        phase_range = end_phase - start_phase
        excess_magi = magi - start_phase
        reduction_ratio = excess_magi / phase_range
        reduction = deduction * reduction_ratio
        return round(deduction - reduction, 2)


def calculate_excess_business_loss(
    net_business_loss: float,
    filing_status: Union[FilingStatus, str] = FilingStatus.SINGLE
) -> float:
    """
    Calculate Excess Business Loss for Form 461 (2024).
    Disallows losses beyond threshold.
    
    Returns the amount to ADD BACK to income (the excess).
    Thresholds:
    - Single/HOH: $305,000
    - MFJ: $610,000
    """
    # net_business_loss is positive if it's a loss (e.g. 400000)
    # If it's a profit, return 0
    if net_business_loss <= 0:
        return 0.0
        
    status = str(filing_status)
    if status == FilingStatus.MARRIED_FILING_JOINTLY:
        threshold = 610000.0
    else:
        threshold = 305000.0
        
    if net_business_loss > threshold:
        return net_business_loss - threshold
    
    return 0.0


if __name__ == "__main__":
    print("Testing Adjustments Toolkit...")
    
    # Test Educator Expense
    print(f"Educator ($400 paid, eligible): {calculate_educator_expense(400, True)}") # Should be 300
    print(f"MFJ Educators ($400 each, both eligible): {calculate_educator_expense(400, True, 400, True, FilingStatus.MARRIED_FILING_JOINTLY)}") # Should be 600
    
    # Test SLI Deduction
    print(f"SLI ($3000 paid, $50k income): {calculate_student_loan_interest(3000, 50000)}") # Should be 2500
    print(f"SLI ($3000 paid, $87.5k income): {calculate_student_loan_interest(3000, 87500)}") # Should be 1250 (halfway)
    print(f"SLI MFJ ($3000 paid, $180k income): {calculate_student_loan_interest(3000, 180000, FilingStatus.MARRIED_FILING_JOINTLY)}") # Should be 1250
    
    # Test EBL
    print(f"EBL Single ($400k loss): {calculate_excess_business_loss(400000, FilingStatus.SINGLE)}") # Should be 95000
    print(f"EBL MFJ ($400k loss): {calculate_excess_business_loss(400000, FilingStatus.MARRIED_FILING_JOINTLY)}") # Should be 0
