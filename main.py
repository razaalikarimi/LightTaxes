"""
Main Entry Point - LightTaxes Tax Agent System
Implements end-to-end tax return processing
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.types import (
    TaxInputs, TaxpayerInfo, FilingStatus, W2,
    Form1099INT, Form1099DIV, BusinessIncome, Dependent,
    Form1040Inputs, ScheduleBInputs
)
from src.agents.form_1040_agent import Form1040Agent
from src.agents.schedule_b_agent import ScheduleBAgent
from src.agents.schedule_c_agent import ScheduleCAgent
from src.agents.schedule_se_agent import ScheduleSEAgent
from src.verifiers.arithmetic_verifier import ArithmeticVerifier
from src.tools.tax_table import calculate_tax
from src.tools.standard_deduction import get_standard_deduction


class TaxReturnProcessor:
    """
    Main orchestrator for tax return processing.
    Coordinates multiple form agents following dependency graph.
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.agents = {}
        self.results = {}
        
        # Initialize agents
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all form agents"""
        self.agents['1040'] = Form1040Agent()
        self.agents['schedule_b'] = ScheduleBAgent()
        self.agents['schedule_c'] = ScheduleCAgent()
        self.agents['schedule_se'] = ScheduleSEAgent()
    
    def _log(self, message: str):
        """Log message if verbose"""
        if self.verbose:
            print(message)
    
    def process_tax_return(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process complete tax return from TaxCalcBench input.json format
        
        Args:
            inputs: Tax return inputs (input.json format)
            
        Returns:
            Form 1040 outputs (output.xml format)
        """
        self._log("=" * 80)
        self._log("Processing Tax Return")
        self._log("=" * 80)
        
        # Parse inputs
        tax_inputs = self._parse_inputs(inputs)
        
        # Process forms in dependency order
        schedule_b_outputs = None
        schedule_c_outputs = None
        schedule_se_outputs = None
        
        # Step 1: Schedule B (if needed)
        if tax_inputs.income_1099_int or tax_inputs.income_1099_div:
            self._log("\n[1/4] Processing Schedule B (Interest & Dividends)...")
            schedule_b_inputs = ScheduleBInputs(
                interest_income=tax_inputs.income_1099_int,
                dividend_income=tax_inputs.income_1099_div
            )
            schedule_b_outputs = self.agents['schedule_b'].process(schedule_b_inputs)
            self._log(f"  Total Interest: ${schedule_b_outputs.total_interest:,.2f}")
            self._log(f"  Total Dividends: ${schedule_b_outputs.total_dividends:,.2f}")
        
        # Step 2: Schedule C (if needed)
        if tax_inputs.business_income:
            self._log("\n[2/4] Processing Schedule C (Business Income)...")
            from src.core.types import ScheduleCInputs
            schedule_c_inputs = ScheduleCInputs(
                business=tax_inputs.business_income,
                filing_status=tax_inputs.filing_status
            )
            schedule_c_outputs = self.agents['schedule_c'].process(schedule_c_inputs)
            self._log(f"  Net Profit/Loss: ${schedule_c_outputs.net_profit_loss:,.2f}")
            
            # Step 3: Schedule SE (if Schedule C has profit)
            if schedule_c_outputs.net_profit_loss > 0:
                self._log("\n[3/4] Processing Schedule SE (Self-Employment Tax)...")
                from src.core.types import ScheduleSEInputs
                schedule_se_inputs = ScheduleSEInputs(
                    net_profit_loss=schedule_c_outputs.net_profit_loss,
                    filing_status=tax_inputs.filing_status
                )
                schedule_se_outputs = self.agents['schedule_se'].process(schedule_se_inputs)
                self._log(f"  SE Tax: ${schedule_se_outputs.self_employment_tax:,.2f}")
                self._log(f"  Deduction: ${schedule_se_outputs.deduction:,.2f}")
        
        # Step 4: Form 1040 (main return)
        self._log(f"\n[4/4] Processing Form 1040 (Main Tax Return)...")
        
        # Calculate total wages from W-2s
        total_wages = sum(w2.wages for w2 in tax_inputs.w2)
        total_withholding = sum(w2.federal_withholding for w2 in tax_inputs.w2)
        
        # Get interest and dividends from Schedule B
        total_interest = schedule_b_outputs.total_interest if schedule_b_outputs else 0
        total_dividends = schedule_b_outputs.total_dividends if schedule_b_outputs else 0
        
        # Prepare Form 1040 inputs
        
        # Calculate Adjustments (Schedule 1)
        from src.tools.adjustments import (
            calculate_educator_expense, 
            calculate_student_loan_interest,
            calculate_excess_business_loss
        )
        
        total_adjustments = 0.0
        se_tax = 0.0
        additional_income = 0.0
        
        # 1. Business Income/Loss
        net_biz = schedule_c_outputs.net_profit_loss if schedule_c_outputs else 0.0
        additional_income += net_biz
        
        # Handle Excess Business Loss (Form 461) - Addition to Income
        if net_biz < 0:
            ebl_addback = calculate_excess_business_loss(abs(net_biz), tax_inputs.filing_status)
            if ebl_addback > 0:
                self._log(f"  Form 461: Excess Business Loss detected. Adding back ${ebl_addback:,.2f}")
                additional_income += ebl_addback # Disallowing loss = adding back
                
        # 2. SE Tax Deduction
        if schedule_se_outputs:
            total_adjustments += schedule_se_outputs.deduction
            se_tax = schedule_se_outputs.self_employment_tax
            
        # 3. Educator Expenses
        educator_deduction = calculate_educator_expense(
            tax_inputs.educator_expenses_paid,
            tax_inputs.taxpayer.is_eligible_educator,
            tax_inputs.spouse_educator_expenses_paid,
            tax_inputs.taxpayer.spouse_eligible_educator,
            tax_inputs.filing_status
        )
        if educator_deduction > 0:
            self._log(f"  Educator Expense Deduction: ${educator_deduction:,.2f}")
            total_adjustments += educator_deduction
            
        # 4. Student Loan Interest (SLI)
        # Temporary MAGI calculation (approximate for deduction lookup)
        temp_agi = total_wages + total_interest + total_dividends + additional_income - (total_adjustments)
        sli_deduction = calculate_student_loan_interest(
            tax_inputs.student_loan_interest_paid,
            temp_agi,
            tax_inputs.filing_status
        )
        if sli_deduction > 0:
            self._log(f"  Student Loan Interest Deduction: ${sli_deduction:,.2f}")
            total_adjustments += sli_deduction
            
        form_1040_inputs = Form1040Inputs(
            filing_status=tax_inputs.filing_status,
            taxpayer=tax_inputs.taxpayer,
            dependents=tax_inputs.dependents,
            wages=total_wages,
            interest=total_interest,
            dividends=total_dividends,
            schedule_1_additional_income=additional_income,
            schedule_1_adjustments=total_adjustments
        )
        
        # Process Form 1040
        form_1040_outputs = self.agents['1040'].process(form_1040_inputs)
        
        # Manually set Line 23 (Other Taxes) since our 1040 agent doesn't fully implement Sch 2 yet
        if se_tax > 0:
            form_1040_outputs.line_23 = se_tax
            # Recalculate total tax (Line 24) since Line 23 changed
            form_1040_outputs.line_24 = form_1040_outputs.line_16 - form_1040_outputs.line_19 + form_1040_outputs.line_23
        
        # Update with withholding info (fix for W-2 integration)
        form_1040_outputs.line_25a = total_withholding
        form_1040_outputs.line_33 = total_withholding
        
        # Recalculate refund/owed
        if form_1040_outputs.line_33 > form_1040_outputs.line_24:
            form_1040_outputs.line_34 = form_1040_outputs.line_33 - form_1040_outputs.line_24
            form_1040_outputs.line_37 = 0
        else:
            form_1040_outputs.line_34 = 0
            form_1040_outputs.line_37 = form_1040_outputs.line_24 - form_1040_outputs.line_33
        
        self._log(f"\n  AGI: ${form_1040_outputs.line_11:,.2f}")
        self._log(f"  Taxable Income: ${form_1040_outputs.line_15:,.2f}")
        self._log(f"  Tax: ${form_1040_outputs.line_16:,.2f}")
        self._log(f"  Total Tax: ${form_1040_outputs.line_24:,.2f}")
        self._log(f"  Payments: ${form_1040_outputs.line_33:,.2f}")
        
        if form_1040_outputs.line_34 > 0:
            self._log(f"  REFUND: ${form_1040_outputs.line_34:,.2f}")
        else:
            self._log(f"  AMOUNT OWED: ${form_1040_outputs.line_37:,.2f}")
        
        # Store results
        self.results = {
            'schedule_b': schedule_b_outputs,
            'schedule_c': schedule_c_outputs,
            'schedule_se': schedule_se_outputs,
            'form_1040': form_1040_outputs
        }
        
        return form_1040_outputs
    
    def verify_results(self) -> bool:
        """
        Run verifiers on the results
        
        Returns:
            True if all verifications pass
        """
        if 'form_1040' not in self.results:
            print("No Form 1040 results to verify")
            return False
        
        self._log("\n" + "=" * 80)
        self._log("Running Verifiers")
        self._log("=" * 80)
        
        # Arithmetic verifier
        verifier = ArithmeticVerifier()
        result = verifier.verify_form_1040(self.results['form_1040'])
        
        self._log(f"\n{result.verifier_name}:")
        self._log(f"  Status: {'✓ PASS' if result.passed else '✗ FAIL'}")
        self._log(f"  Errors: {len(result.errors)}")
        self._log(f"  Warnings: {len(result.warnings)}")
        
        if result.errors:
            self._log("\n  Errors Found:")
            for error in result.errors:
                self._log(f"    - {error.line}: {error.message}")
        
        if result.warnings:
            self._log("\n  Warnings:")
            for warning in result.warnings:
                self._log(f"    - {warning}")
        
        return result.passed
    
    def _parse_inputs(self, data: Dict[str, Any]) -> TaxInputs:
        """Parse input.json format to typed inputs"""
        
        # Parse filing status
        filing_status_map = {
            "single": FilingStatus.SINGLE,
            "married_filing_jointly": FilingStatus.MARRIED_FILING_JOINTLY,
            "married_filing_separately": FilingStatus.MARRIED_FILING_SEPARATELY,
            "head_of_household": FilingStatus.HEAD_OF_HOUSEHOLD,
            "qualifying_widow": FilingStatus.QUALIFYING_WIDOW,
        }
        
        filing_status = filing_status_map.get(
            data.get("filing_status", "single").lower(),
            FilingStatus.SINGLE
        )
        
        # Parse taxpayer info
        taxpayer = TaxpayerInfo(
            name=data.get("taxpayer_name", "Taxpayer"),
            ssn=data.get("ssn", "000-00-0000"),
            age=data.get("age")
        )
        
        # Parse W-2s
        w2s = []
        if "w2" in data:
            for w2_data in data["w2"]:
                w2s.append(W2(
                    wages=w2_data.get("wages", 0),
                    federal_withholding=w2_data.get("federal_withholding", 0)
                ))
        
        # Parse 1099-INT
        interest_forms = []
        if "income_1099_int" in data:
            for form_data in data["income_1099_int"]:
                interest_forms.append(Form1099INT(
                    interest_income=form_data.get("interest_income", 0)
                ))
        
        # Parse dependents
        dependents = []
        if "dependents" in data:
            for dep_data in data["dependents"]:
                dependents.append(Dependent(
                    name=dep_data.get("name", ""),
                    ssn=dep_data.get("ssn", ""),
                    relationship=dep_data.get("relationship", ""),
                    qualifying_child=dep_data.get("qualifying_child", False)
                ))
        
        # Parse Business Income (Schedule C)
        business_income = None
        if "business_income" in data:
            biz_data = data["business_income"]
            business_income = BusinessIncome(
                business_name=biz_data.get("business_name"),
                gross_receipts=biz_data.get("gross_receipts", 0),
                advertising=biz_data.get("advertising", 0),
                office_expense=biz_data.get("office_expense", 0),
                supplies=biz_data.get("supplies", 0),
                utilities=biz_data.get("utilities", 0),
                meals=biz_data.get("meals", 0),
                legal_professional=biz_data.get("legal_professional", 0),
                other_expenses=biz_data.get("other_expenses", {})
            )
        
        # Standard Educator Expense & SLI extraction from input
        educator_expenses_paid = data.get("educator_expenses_paid", 0.0)
        spouse_educator_expenses_paid = data.get("spouse_educator_expenses_paid", 0.0)
        student_loan_interest_paid = data.get("student_loan_interest_paid", 0.0)
        
        # Check flags for eligibility
        taxpayer.is_eligible_educator = data.get("is_taxpayer_educator", False)
        taxpayer.spouse_eligible_educator = data.get("is_spouse_educator", False)
        
        return TaxInputs(
            filing_status=filing_status,
            taxpayer=taxpayer,
            dependents=dependents,
            w2=w2s,
            income_1099_int=interest_forms,
            business_income=business_income,
            educator_expenses_paid=educator_expenses_paid,
            spouse_educator_expenses_paid=spouse_educator_expenses_paid,
            student_loan_interest_paid=student_loan_interest_paid
        )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="LightTaxes - Codebase-Style Tax Agent System"
    )
    parser.add_argument(
        "--case",
        type=str,
        default="single-w2",
        help="TaxCalcBench test case name (e.g., single-w2, mfj-w2)"
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Path to input.json file"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Path to save output.xml"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run verifiers"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in mock mode (no API key needed)"
    )
    
    args = parser.parse_args()
    
    # Set mock mode if requested
    if args.mock:
        os.environ["DEFAULT_LLM"] = "mock"
        print("\n⚠️  RUNNING IN MOCK MODE - Results will be simulated")
    
    # Determine input file
    if args.input:
        input_file = Path(args.input)
    else:
        input_file = Path(f"data/tax_calc_bench/{args.case}/input.json")
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        print("\nCreating example input file for testing...")
        
        # Create example input
        example_input = {
            "filing_status": "single",
            "taxpayer_name": "John Doe",
            "ssn": "123-45-6789",
            "w2": [
                {
                    "wages": 50000,
                    "federal_withholding": 5000
                }
            ]
        }
        
        # Use it directly
        input_data = example_input
    else:
        with open(input_file, 'r') as f:
            input_data = json.load(f)
    
    # Process tax return
    processor = TaxReturnProcessor(verbose=args.verbose or True)
    result = processor.process_tax_return(input_data)
    
    # Verify if requested
    if args.verify:
        passed = processor.verify_results()
        if not passed:
            print("\n⚠️  Verification failed!")
            sys.exit(1)
        else:
            print("\n✓ All verifications passed!")
    
    # Print summary
    print("\n" + "=" * 80)
    print("FORM 1040 - U.S. INDIVIDUAL INCOME TAX RETURN")
    print("=" * 80)
    print(f"\nLine 1z  - Wages:                    ${result.line_1z:>15,.2f}")
    print(f"Line 2b  - Interest:                 ${result.line_2b:>15,.2f}")
    print(f"Line 3b  - Dividends:                ${result.line_3b:>15,.2f}")
    print(f"Line 9   - Total Income:             ${result.line_9:>15,.2f}")
    print(f"Line 11  - AGI:                      ${result.line_11:>15,.2f}")
    print(f"Line 12  - Deductions:               ${result.line_12:>15,.2f}")
    print(f"Line 15  - Taxable Income:           ${result.line_15:>15,.2f}")
    print(f"Line 16  - Tax:                      ${result.line_16:>15,.2f}")
    print(f"Line 19  - Child Tax Credit:         ${result.line_19:>15,.2f}")
    print(f"Line 24  - Total Tax:                ${result.line_24:>15,.2f}")
    print(f"Line 33  - Total Payments:           ${result.line_33:>15,.2f}")
    print("-" * 80)
    
    if result.line_34 > 0:
        print(f"Line 34  - REFUND:                   ${result.line_34:>15,.2f} ✓")
    else:
        print(f"Line 37  - Amount Owed:              ${result.line_37:>15,.2f}")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
