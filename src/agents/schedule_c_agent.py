"""
Schedule C Agent - Profit or Loss from Business
Upstream form for Schedule SE (self-employment tax)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.core.form_agent import FormAgent
from src.core.types import ScheduleCInputs, ScheduleCOutputs


class ScheduleCAgent(FormAgent):
    """
    Schedule C - Profit or Loss from Business (Sole Proprietorship)
    
    Dependencies:
    - Input: Business income and expenses
    - Output: Net profit/loss → Schedule SE → Schedule 1
    """
    
    def __init__(self, **kwargs):
        super().__init__(form_name="schedule-c", **kwargs)
    
    def process(self, inputs: ScheduleCInputs) -> ScheduleCOutputs:
        """
        Process Schedule C
        
        Part I - Income (Lines 1-7)
        Part II - Expenses (Lines 8-27)
        Part III - Cost of Goods Sold (not implemented)
        
        Args:
            inputs: ScheduleCInputs with business data
            
        Returns:
            ScheduleCOutputs with gross income, expenses, and net profit/loss
        """
        business = inputs.business
        
        # Part I: Income
        # Line 1: Gross receipts
        gross_receipts = business.gross_receipts
        
        # Line 2: Returns and allowances
        returns = business.returns_allowances
        
        # Line 4: Cost of goods sold
        cogs = business.cost_of_goods_sold
        
        # Line 7: Gross income
        gross_income = gross_receipts - returns - cogs + business.other_income
        
        self.cite(
            "Line 7",
            "Schedule C Instructions, Part I",
            f"Gross income: ${gross_income:,.2f} = Receipts (${gross_receipts:,.2f}) - Returns (${returns:,.2f}) - COGS (${cogs:,.2f}) + Other (${business.other_income:,.2f})"
        )
        
        # Part II: Expenses
        total_expenses = (
            business.advertising +
            business.car_truck_expenses +
            business.commissions_fees +
            business.contract_labor +
            business.depreciation +
            business.insurance +
            business.interest +
            business.legal_professional +
            business.office_expense +
            business.rent_lease +
            business.repairs_maintenance +
            business.supplies +
            business.taxes_licenses +
            business.travel +
            (business.meals * 0.5) +  # Only 50% of meals deductible
            business.utilities +
            business.wages +
            sum(business.other_expenses.values())
        )
        
        self.cite(
            "Line 28",
            "Schedule C Instructions, Part II",
            f"Total expenses: ${total_expenses:,.2f} (Note: Meals limited to 50% deductible)"
        )
        
        # Line 31: Net profit or loss
        net_profit_loss = gross_income - total_expenses
        
        self.cite(
            "Line 31",
            "Schedule C Instructions, Line 31",
            f"Net profit (or loss): ${net_profit_loss:,.2f} = Gross Income (${gross_income:,.2f}) - Total Expenses (${total_expenses:,.2f})"
        )
        
        outputs = ScheduleCOutputs(
            gross_income=gross_income,
            total_expenses=total_expenses,
            net_profit_loss=net_profit_loss
        )
        
        outputs.citations = {c.line: c.source for c in self.citations}
        
        return outputs


if __name__ == "__main__":
    from src.core.types import BusinessIncome, FilingStatus
    
    print("Testing Schedule C Agent...")
    print("=" * 80)
    
    # Test case: simple business
    business = BusinessIncome(
        business_name="Web Design Services",
        gross_receipts=75000,
        advertising=2000,
        office_expense=1500,
        supplies=800,
        utilities=1200,
        meals=500
    )
    
    inputs = ScheduleCInputs(
        business=business,
        filing_status=FilingStatus.SINGLE
    )
    
    agent = ScheduleCAgent()
    outputs = agent.process(inputs)
    
    print("\nSchedule C Results:")
    print("-" * 80)
    print(f"Gross Income (Line 7):       ${outputs.gross_income:>12,.2f}")
    print(f"Total Expenses (Line 28):    ${outputs.total_expenses:>12,.2f}")
    print(f"Net Profit/Loss (Line 31):   ${outputs.net_profit_loss:>12,.2f}")
    
    print("\nCitations:")
    print("-" * 80)
    for citation in agent.citations:
        print(f"{citation.line}: {citation.reasoning}")
