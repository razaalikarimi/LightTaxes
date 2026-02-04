"""
Schedule B Agent - Interest and Ordinary Dividends
Upstream form for Form 1040 (feeds Lines 2b and 3b)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.core.form_agent import FormAgent
from src.core.types import ScheduleBInputs, ScheduleBOutputs


class ScheduleBAgent(FormAgent):
    """
    Schedule B - Interest and Ordinary Dividends
    
    Dependencies:
    - Input: Form 1099-INT, Form 1099-DIV
    - Output: Form 1040 Lines 2b and 3b
    """
    
    def __init__(self, **kwargs):
        super().__init__(form_name="schedule-b", **kwargs)
    
    def process(self, inputs: ScheduleBInputs) -> ScheduleBOutputs:
        """
        Process Schedule B
        
        Part I - Interest (Lines 1-4)
        Part II - Ordinary Dividends (Lines 5-6)
        Part III - Foreign Accounts (not implemented)
        
        Args:
            inputs: ScheduleBInputs with 1099-INT and 1099-DIV data
            
        Returns:
            ScheduleBOutputs with total interest and dividends
        """
        outputs = ScheduleBOutputs(
            total_interest=0.0,
            total_dividends=0.0
        )
        
        # Part I: Interest
        if inputs.interest_income:
            outputs.total_interest = sum(
                item.interest_income for item in inputs.interest_income
            )
            
            self.cite(
                "Line 4",
                "Form 1099-INT aggregation",
                f"Total interest income: ${outputs.total_interest:,.2f} from {len(inputs.interest_income)} payer(s)"
            )
        
        # Part II: Dividends
        if inputs.dividend_income:
            outputs.total_dividends = sum(
                item.ordinary_dividends for item in inputs.dividend_income
            )
            
            self.cite(
                "Line 6",
                "Form 1099-DIV aggregation",
                f"Total ordinary dividends: ${outputs.total_dividends:,.2f} from {len(inputs.dividend_income)} payer(s)"
            )
        
        # Add citations to outputs
        outputs.citations = {c.line: c.source for c in self.citations}
        
        return outputs


if __name__ == "__main__":
    from src.core.types import Form1099INT, Form1099DIV
    
    print("Testing Schedule B Agent...")
    print("=" * 80)
    
    # Test case with interest and dividends
    inputs = ScheduleBInputs(
        interest_income=[
            Form1099INT(payer="Bank of America", interest_income=150.50),
            Form1099INT(payer="Chase Bank", interest_income=75.25)
        ],
        dividend_income=[
            Form1099DIV(payer="Vanguard", ordinary_dividends=500.00, qualified_dividends=500.00)
        ]
    )
    
    agent = ScheduleBAgent()
    outputs = agent.process(inputs)
    
    print("\nSchedule B Results:")
    print("-" * 80)
    print(f"Total Interest (Line 4):    ${outputs.total_interest:>12,.2f}")
    print(f"Total Dividends (Line 6):   ${outputs.total_dividends:>12,.2f}")
    
    print("\nCitations:")
    print("-" * 80)
    for citation in agent.citations:
        print(f"{citation.line}: {citation.reasoning}")
