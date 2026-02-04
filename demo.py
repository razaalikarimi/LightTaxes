"""
Simple Demo - Shows tax calculation without needing API key
Demonstrates the deterministic calculation pipeline
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tools.tax_table import calculate_tax
from src.tools.standard_deduction import get_standard_deduction

def demo_tax_calculation(wages, withholding, filing_status, name="Taxpayer"):
    """
    Demonstrate complete tax calculation flow
    """
    print("=" * 80)
    print(f"TAX CALCULATION DEMO - {name}")
    print("=" * 80)
    print()
    
    # Step 1: Income
    print("STEP 1: INCOME")
    print("-" * 80)
    print(f"W-2 Wages (Line 1z):                    ${wages:>15,.2f}")
    total_income = wages
    print(f"Total Income (Line 9):                  ${total_income:>15,.2f}")
    print()
    
    # Step 2: Adjustments (none in this simple case)
    print("STEP 2: ADJUSTMENTS")
    print("-" * 80)
    adjustments = 0
    print(f"Adjustments to Income (Line 10):        ${adjustments:>15,.2f}")
    print()
    
    # Step 3: AGI
    print("STEP 3: ADJUSTED GROSS INCOME (AGI)")
    print("-" * 80)
    agi = total_income - adjustments
    print(f"AGI (Line 11):                          ${agi:>15,.2f}")
    print(f"  Calculation: ${total_income:,.2f} - ${adjustments:,.2f}")
    print()
    
    # Step 4: Deductions
    print("STEP 4: DEDUCTIONS")
    print("-" * 80)
    std_deduction = get_standard_deduction(filing_status)
    print(f"Standard Deduction (Line 12):           ${std_deduction:>15,.2f}")
    print(f"  Filing Status: {filing_status}")
    print()
    
    # Step 5: Taxable Income
    print("STEP 5: TAXABLE INCOME")
    print("-" * 80)
    taxable_income = max(0, agi - std_deduction)
    print(f"Taxable Income (Line 15):               ${taxable_income:>15,.2f}")
    print(f"  Calculation: ${agi:,.2f} - ${std_deduction:,.2f}")
    print()
    
    # Step 6: Tax Calculation (DETERMINISTIC - from IRS tables)
    print("STEP 6: TAX CALCULATION")
    print("-" * 80)
    tax = calculate_tax(taxable_income, filing_status)
    print(f"Tax (Line 16):                          ${tax:>15,.2f}")
    print(f"  Using 2024 IRS Tax Tables")
    print(f"  Taxable Income: ${taxable_income:,.2f}")
    print(f"  Filing Status: {filing_status}")
    print()
    
    # Step 7: Credits (none in this simple case)
    print("STEP 7: CREDITS")
    print("-" * 80)
    credits = 0
    print(f"Child Tax Credit (Line 19):             ${credits:>15,.2f}")
    print()
    
    # Step 8: Total Tax
    print("STEP 8: TOTAL TAX")
    print("-" * 80)
    total_tax = tax - credits
    print(f"Total Tax (Line 24):                    ${total_tax:>15,.2f}")
    print(f"  Calculation: ${tax:,.2f} - ${credits:,.2f}")
    print()
    
    # Step 9: Payments
    print("STEP 9: PAYMENTS")
    print("-" * 80)
    print(f"Federal Tax Withheld (Line 25a):        ${withholding:>15,.2f}")
    print(f"Total Payments (Line 33):               ${withholding:>15,.2f}")
    print()
    
    # Step 10: Refund or Amount Owed
    print("STEP 10: REFUND OR AMOUNT OWED")
    print("-" * 80)
    
    if withholding > total_tax:
        refund = withholding - total_tax
        amount_owed = 0
        print(f"REFUND (Line 34):                       ${refund:>15,.2f} ✓")
        print(f"  You overpaid by ${refund:,.2f}")
        result = f"REFUND: ${refund:,.2f}"
    else:
        refund = 0
        amount_owed = total_tax - withholding
        print(f"Amount You Owe (Line 37):               ${amount_owed:>15,.2f}")
        print(f"  You underpaid by ${amount_owed:,.2f}")
        result = f"OWED: ${amount_owed:,.2f}"
    
    print()
    print("=" * 80)
    print(f"FINAL RESULT: {result}")
    print("=" * 80)
    print()
    
    return {
        'wages': wages,
        'agi': agi,
        'taxable_income': taxable_income,
        'tax': tax,
        'total_tax': total_tax,
        'withholding': withholding,
        'refund': refund,
        'amount_owed': amount_owed
    }


if __name__ == "__main__":
    print("\n🎯 LIGHTTAXES TAX CALCULATION SYSTEM")
    print("Demonstrating Deterministic Tax Calculation Pipeline")
    print("(No API key needed - uses pure IRS tax formulas)\n")
    
    # Demo 1: Single W-2 filer (from test case)
    print("\n" + "█" * 80)
    print("DEMO 1: Single Filer with W-2")
    print("█" * 80 + "\n")
    
    result1 = demo_tax_calculation(
        wages=50000,
        withholding=5000,
        filing_status="single",
        name="John Doe"
    )
    
    # Demo 2: Married Filing Jointly (from test case)
    print("\n" + "█" * 80)
    print("DEMO 2: Married Filing Jointly with Dual Income")
    print("█" * 80 + "\n")
    
    result2 = demo_tax_calculation(
        wages=105000,  # 60000 + 45000 from input.json
        withholding=10500,  # 6000 + 4500
        filing_status="married_filing_jointly",
        name="John & Jane Smith"
    )
    
    # Summary comparison
    print("\n" + "█" * 80)
    print("COMPARISON SUMMARY")
    print("█" * 80 + "\n")
    
    print(f"{'Metric':<30} {'Single':<20} {'MFJ':<20}")
    print("-" * 80)
    print(f"{'Wages':<30} ${result1['wages']:>18,.2f} ${result2['wages']:>18,.2f}")
    print(f"{'AGI':<30} ${result1['agi']:>18,.2f} ${result2['agi']:>18,.2f}")
    print(f"{'Taxable Income':<30} ${result1['taxable_income']:>18,.2f} ${result2['taxable_income']:>18,.2f}")
    print(f"{'Tax':<30} ${result1['tax']:>18,.2f} ${result2['tax']:>18,.2f}")
    print(f"{'Withholding':<30} ${result1['withholding']:>18,.2f} ${result2['withholding']:>18,.2f}")
    
    if result1['refund'] > 0:
        print(f"{'Refund':<30} ${result1['refund']:>18,.2f} ✓", end="")
    else:
        print(f"{'Amount Owed':<30} ${result1['amount_owed']:>18,.2f}", end="")
    
    if result2['refund'] > 0:
        print(f" ${result2['refund']:>18,.2f} ✓")
    else:
        print(f" ${result2['amount_owed']:>18,.2f}")
    
    print()
    print("=" * 80)
    print("✅ ALL CALCULATIONS COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print("\nNote: This demo uses 100% deterministic calculations from IRS 2024 tax tables.")
    print("No LLM/API needed for these calculations - pure Python functions!")
    print("\nFor full system with IRS PDF grounding and LLM reasoning,")
    print("add your API key to .env and run: python main.py --case single-w2 --verbose")
    print()
