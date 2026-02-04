"""
Form 1040 Agent - U.S. Individual Income Tax Return
This is the main tax return form - analogous to main() in the paper's codebase metaphor
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.core.form_agent import FormAgent
from src.core.types import Form1040Inputs, Form1040Outputs
from src.tools.tax_table import calculate_tax
from src.tools.standard_deduction import get_standard_deduction


class Form1040Agent(FormAgent):
    """
    Form 1040 - U.S. Individual Income Tax Return
    
    This is the core tax return form. It integrates inputs from:
    - W-2 (wages)
    - Schedule B (interest/dividends)
    - Schedule 1 (additional income/adjustments)
    - Schedule SE (self-employment tax)
    - Schedule 8812 (child tax credit)
    """
    
    def __init__(self, **kwargs):
        super().__init__(form_name="1040", **kwargs)
    
    def process(self, inputs: Form1040Inputs) -> Form1040Outputs:
        """
        Process Form 1040
        
        Flow:
        1. Calculate total income (Lines 1-9)
        2. Apply adjustments (Line 10)
        3. Calculate AGI (Line 11)
        4. Apply deductions (Line 12)
        5. Calculate taxable income (Line 15)
        6. Calculate tax (Line 16)
        7. Apply credits (Lines 17-21)
        8. Calculate total tax (Line 24)
        9. Calculate payments (Lines 25-32)
        10. Determine refund or amount owed (Lines 34/37)
        
        Args:
            inputs: Form1040Inputs with all required data
            
        Returns:
            Form1040Outputs with all calculated lines
        """
        outputs = Form1040Outputs()
        
        # INCOME SECTION (Lines 1-9)
        self._calculate_income(inputs, outputs)
        
        # ADJUSTMENTS (Line 10)
        self._calculate_adjustments(inputs, outputs)
        
        # AGI (Line 11)
        self._calculate_agi(inputs, outputs)
        
        # DEDUCTIONS (Line 12)
        self._calculate_deductions(inputs, outputs)
        
        # TAXABLE INCOME (Line 15)
        self._calculate_taxable_income(inputs, outputs)
        
        # TAX (Line 16)
        self._calculate_tax(inputs, outputs)
        
        # CREDITS (Lines 17-21)
        self._calculate_credits(inputs, outputs)
        
        # OTHER TAXES (Lines 22-23)
        self._calculate_other_taxes(inputs, outputs)
        
        # TOTAL TAX (Line 24)
        self._calculate_total_tax(inputs, outputs)
        
        # PAYMENTS (Lines 25-33)
        self._calculate_payments(inputs, outputs)
        
        # REFUND OR AMOUNT OWED (Lines 34/37)
        self._calculate_refund_or_owed(inputs, outputs)
        
        # Add citations
        outputs.citations = {c.line: c.source for c in self.citations}
        
        return outputs
    
    def _calculate_income(self, inputs: Form1040Inputs, outputs: Form1040Outputs):
        """Calculate total income (Lines 1-9)"""
        
        # Line 1z: Wages from W-2
        outputs.line_1z = inputs.wages
        self.cite(
            "Line 1z",
            "Form W-2, Box 1",
            f"Total wages from W-2 forms: ${outputs.line_1z:,.2f}"
        )
        
        # Line 2b: Taxable interest (from Schedule B or direct input)
        outputs.line_2b = inputs.interest
        if outputs.line_2b > 0:
            self.cite(
                "Line 2b",
                "Schedule B, Line 4 or Form 1099-INT",
                f"Taxable interest income: ${outputs.line_2b:,.2f}"
            )
        
        # Line 3b: Qualified dividends (from Schedule B or direct input)
        outputs.line_3b = inputs.dividends
        if outputs.line_3b > 0:
            self.cite(
                "Line 3b",
                "Schedule B, Line 6 or Form 1099-DIV",
                f"Qualified dividends: ${outputs.line_3b:,.2f}"
            )
        
        # Line 8: Additional income from Schedule 1
        outputs.line_8 = inputs.schedule_1_additional_income
        if outputs.line_8 > 0:
            self.cite(
                "Line 8",
                "Schedule 1, Line 10",
                f"Additional income from Schedule 1: ${outputs.line_8:,.2f}"
            )
        
        # Line 9: Total income
        outputs.line_9 = (
            outputs.line_1z +
            outputs.line_2b +
            outputs.line_3b +
            outputs.line_8
        )
        self.cite(
            "Line 9",
            "Form 1040 Instructions, Line 9",
            f"Total income: ${outputs.line_9:,.2f} = Sum of Lines 1-8"
        )
    
    def _calculate_adjustments(self, inputs: Form1040Inputs, outputs: Form1040Outputs):
        """Calculate adjustments to income (Line 10)"""
        
        # Line 10: Adjustments from Schedule 1
        outputs.line_10 = inputs.schedule_1_adjustments
        if outputs.line_10 > 0:
            self.cite(
                "Line 10",
                "Schedule 1, Line 26",
                f"Adjustments to income from Schedule 1: ${outputs.line_10:,.2f}"
            )
    
    def _calculate_agi(self, inputs: Form1040Inputs, outputs: Form1040Outputs):
        """Calculate Adjusted Gross Income (Line 11)"""
        
        # Line 11: AGI = Total Income - Adjustments
        outputs.line_11 = outputs.line_9 - outputs.line_10
        self.cite(
            "Line 11",
            "Form 1040 Instructions, Line 11 - Adjusted Gross Income",
            f"AGI: ${outputs.line_11:,.2f} = Line 9 (${outputs.line_9:,.2f}) - Line 10 (${outputs.line_10:,.2f})"
        )
    
    def _calculate_deductions(self, inputs: Form1040Inputs, outputs: Form1040Outputs):
        """Calculate deductions (Line 12)"""
        
        # Line 12: Standard or itemized deduction
        # For this implementation, always use standard deduction
        # In production, would check Schedule A
        
        taxpayer_age = inputs.taxpayer.age
        taxpayer_blind = inputs.taxpayer.blind
        spouse_age = inputs.taxpayer.spouse_age
        spouse_blind = inputs.taxpayer.spouse_blind
        
        outputs.line_12 = get_standard_deduction(
            inputs.filing_status.value,
            taxpayer_age,
            taxpayer_blind,
            spouse_age,
            spouse_blind
        )
        
        self.cite(
            "Line 12",
            f"IRS Standard Deduction for {inputs.filing_status.value}",
            f"Standard deduction: ${outputs.line_12:,.2f}"
        )
    
    def _calculate_taxable_income(self, inputs: Form1040Inputs, outputs: Form1040Outputs):
        """Calculate taxable income (Line 15)"""
        
        # Line 15: Taxable income = AGI - Deductions
        # Note: Line 13 (qualified business income deduction) skipped for simplicity
        # Line 14 would be sum of 12 and 13
        outputs.line_15 = max(0, outputs.line_11 - outputs.line_12)
        
        self.cite(
            "Line 15",
            "Form 1040 Instructions, Line 15 - Taxable Income",
            f"Taxable income: ${outputs.line_15:,.2f} = AGI (${outputs.line_11:,.2f}) - Deductions (${outputs.line_12:,.2f})"
        )
    
    def _calculate_tax(self, inputs: Form1040Inputs, outputs: Form1040Outputs):
        """Calculate tax using deterministic tax table (Line 16)"""
        
        # Line 16: Tax from tax table or computation worksheet
        # This uses DETERMINISTIC calculation - NO LLM
        outputs.line_16 = calculate_tax(outputs.line_15, inputs.filing_status.value)
        
        self.cite(
            "Line 16",
            "2024 Tax Computation Worksheet / Tax Tables",
            f"Tax on ${outputs.line_15:,.2f} taxable income with {inputs.filing_status.value} status: ${outputs.line_16:,.2f}"
        )
    
    def _calculate_credits(self, inputs: Form1040Inputs, outputs: Form1040Outputs):
        """Calculate credits (Lines 17-21)"""
        
        # Line 19: Child tax credit (from Schedule 8812 or simple calc)
        # For simplicity, not implementing full Schedule 8812 logic here
        # In production, would call Schedule8812Agent
        
        num_qualifying_children = sum(1 for d in inputs.dependents if d.qualifying_child)
        
        if num_qualifying_children > 0:
            # Simple child tax credit (not considering phase-outs)
            # $2000 per qualifying child
            child_credit = num_qualifying_children * 2000
            # Credit cannot exceed tax
            outputs.line_19 = min(child_credit, outputs.line_16)
            
            self.cite(
                "Line 19",
                "Schedule 8812 - Child Tax Credit",
                f"Child tax credit: ${outputs.line_19:,.2f} for {num_qualifying_children} qualifying children"
            )
    
    def _calculate_other_taxes(self, inputs: Form1040Inputs, outputs: Form1040Outputs):
        """Calculate other taxes (Lines 22-23)"""
        
        # Line 23: Self-employment tax (from Schedule SE via Schedule 1)
        # This would come from Schedule 1, but we'll track it separately
        # In production, this would be properly integrated
        pass
    
    def _calculate_total_tax(self, inputs: Form1040Inputs, outputs: Form1040Outputs):
        """Calculate total tax (Line 24)"""
        
        # Line 24: Total tax = Tax - Credits + Other Taxes
        # Simplified: Line 16 - Line 19 + Line 23
        outputs.line_24 = outputs.line_16 - outputs.line_19 + outputs.line_23
        
        self.cite(
            "Line 24",
            "Form 1040 Instructions, Line 24 - Total Tax",
            f"Total tax: ${outputs.line_24:,.2f} = Tax (${outputs.line_16:,.2f}) - Credits (${outputs.line_19:,.2f}) + Other Taxes (${outputs.line_23:,.2f})"
        )
    
    def _calculate_payments(self, inputs: Form1040Inputs, outputs: Form1040Outputs):
        """Calculate payments (Lines 25-33)"""
        
        # Line 25a: Federal income tax withheld from W-2
        # Sum all W-2 withholding from inputs
        total_withholding = sum(w2.federal_withholding for w2 in inputs.taxpayer.w2) if hasattr(inputs.taxpayer, 'w2') else 0
        
        # If no W-2 info in taxpayer, check if wages input includes withholding info
        # For TaxCalcBench compatibility, we might need to extract from initial inputs
        # For now, we'll set this to 0 unless explicitly provided
        outputs.line_25a = total_withholding
        
        if outputs.line_25a > 0:
            self.cite(
                "Line 25a",
                "Form W-2, Box 2",
                f"Federal income tax withheld: ${outputs.line_25a:,.2f}"
            )
        
        # Line 33: Total payments
        outputs.line_33 = outputs.line_25a
        
        self.cite(
            "Line 33",
            "Form 1040 Instructions, Line 33 - Total Payments",
            f"Total payments: ${outputs.line_33:,.2f}"
        )
    
    def _calculate_refund_or_owed(self, inputs: Form1040Inputs, outputs: Form1040Outputs):
        """Calculate refund or amount owed (Lines 34/37)"""
        
        # Compare payments to total tax
        if outputs.line_33 > outputs.line_24:
            # Refund
            outputs.line_34 = outputs.line_33 - outputs.line_24
            outputs.line_37 = 0
            
            self.cite(
                "Line 34",
                "Form 1040 Instructions, Line 34 - Refund",
                f"Overpayment (refund): ${outputs.line_34:,.2f} = Payments (${outputs.line_33:,.2f}) - Tax (${outputs.line_24:,.2f})"
            )
        else:
            # Amount owed
            outputs.line_34 = 0
            outputs.line_37 = outputs.line_24 - outputs.line_33
            
            self.cite(
                "Line 37",
                "Form 1040 Instructions, Line 37 - Amount You Owe",
                f"Amount you owe: ${outputs.line_37:,.2f} = Tax (${outputs.line_24:,.2f}) - Payments (${outputs.line_33:,.2f})"
            )


if __name__ == "__main__":
    # Test Form 1040 Agent
    from src.core.types import TaxpayerInfo, FilingStatus, W2
    
    print("Testing Form 1040 Agent...")
    print("=" * 80)
    
    # Simple test case: single filer with W-2
    taxpayer = TaxpayerInfo(
        name="John Doe",
        ssn="123-45-6789",
        age=35
    )
    
    inputs = Form1040Inputs(
        filing_status=FilingStatus.SINGLE,
        taxpayer=taxpayer,
        wages=50000.0,
        interest=0.0,
        dividends=0.0,
        schedule_1_additional_income=0.0,
        schedule_1_adjustments=0.0
    )
    
    agent = Form1040Agent()
    outputs = agent.process(inputs)
    
    print("\nForm 1040 Results:")
    print("-" * 80)
    print(f"Line 1z (Wages):             ${outputs.line_1z:>12,.2f}")
    print(f"Line 9  (Total Income):      ${outputs.line_9:>12,.2f}")
    print(f"Line 11 (AGI):               ${outputs.line_11:>12,.2f}")
    print(f"Line 12 (Deductions):        ${outputs.line_12:>12,.2f}")
    print(f"Line 15 (Taxable Income):    ${outputs.line_15:>12,.2f}")
    print(f"Line 16 (Tax):               ${outputs.line_16:>12,.2f}")
    print(f"Line 24 (Total Tax):         ${outputs.line_24:>12,.2f}")
    print(f"Line 33 (Payments):          ${outputs.line_33:>12,.2f}")
    print(f"Line 34 (Refund):            ${outputs.line_34:>12,.2f}")
    print(f"Line 37 (Amount Owed):       ${outputs.line_37:>12,.2f}")
    
    print("\nCitations:")
    print("-" * 80)
    for citation in agent.citations[:5]:  # Show first 5
        print(f"{citation.line}: {citation.reasoning}")
