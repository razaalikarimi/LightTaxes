"""
Schedule SE Agent - Self-Employment Tax
Calculates Social Security and Medicare tax for self-employed individuals
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.core.form_agent import FormAgent
from src.core.types import ScheduleSEInputs, ScheduleSEOutputs


# 2024 Self-Employment Tax Constants
SE_TAX_RATE = 0.9235  # 92.35% of net earnings subject to SE tax
SOCIAL_SECURITY_RATE = 0.124   # 12.4%
MEDICARE_RATE = 0.029  # 2.9%
TOTAL_SE_RATE = SOCIAL_SECURITY_RATE + MEDICARE_RATE  # 15.3%
SOCIAL_SECURITY_WAGE_BASE_2024 = 168600  # Wage base limit for Social Security


class ScheduleSEAgent(FormAgent):
    """
    Schedule SE - Self-Employment Tax
    
    Dependencies:
    - Input: Net profit from Schedule C
    - Output: 
        - Self-employment tax → Form 1040 Schedule 1 Line 15
        - Deduction (1/2 of SE tax) → Form 1040 Schedule 1 Line 15
    """
    
    def __init__(self, **kwargs):
        super().__init__(form_name="schedule-se", **kwargs)
    
    def process(self, inputs: ScheduleSEInputs) -> ScheduleSEOutputs:
        """
        Process Schedule SE (Short Schedule SE - Section A)
        
        Part I - Self-Employment Tax (Lines 1-13)
        
        Args:
            inputs: ScheduleSEInputs with net profit from Schedule C
            
        Returns:
            ScheduleSEOutputs with SE tax and deduction
        """
        
        net_profit = inputs.net_profit_loss
        
        # Must have net profit to have SE tax
        if net_profit <= 400:
            # No SE tax if net earnings < $400
            outputs = ScheduleSEOutputs(
                net_earnings=0.0,
                self_employment_tax=0.0,
                deduction=0.0
            )
            
            self.cite(
                "Schedule SE",
                "IRS Instructions: Net earnings < $400",
                "No self-employment tax due (net earnings below $400 threshold)"
            )
            
            return outputs
        
        # Line 4: Net earnings from self-employment
        # Multiply net profit by 92.35%
        net_earnings = net_profit * SE_TAX_RATE
        
        self.cite(
            "Line 4",
            "Schedule SE Instructions, Line 4",
            f"Net earnings: ${net_earnings:,.2f} = ${net_profit:,.2f} × 92.35%"
        )
        
        # Calculate Social Security and Medicare portions
        # Line 5-6: Social Security (12.4% up to wage base)
        ss_earnings = min(net_earnings, SOCIAL_SECURITY_WAGE_BASE_2024)
        ss_tax = ss_earnings * SOCIAL_SECURITY_RATE
        
        # Line 7-8: Medicare (2.9% on all earnings)
        medicare_tax = net_earnings * MEDICARE_RATE
        
        # Line 12: Total self-employment tax
        self_employment_tax = ss_tax + medicare_tax
        
        self.cite(
            "Line 12",
            "Schedule SE Instructions, Line 12",
            f"Self-employment tax: ${self_employment_tax:,.2f} = SS (${ss_tax:,.2f}) + Medicare (${medicare_tax:,.2f})"
        )
        
        # Line 13: Deduction for 1/2 of SE tax
        # This goes to Schedule 1 Line 15
        deduction = self_employment_tax / 2
        
        self.cite(
            "Line 13",
            "Schedule SE Instructions, Line 13 - Deduction",
            f"Deduction for 1/2 of SE tax: ${deduction:,.2f}"
        )
        
        outputs = ScheduleSEOutputs(
            net_earnings=net_earnings,
            self_employment_tax=round(self_employment_tax, 2),
            deduction=round(deduction, 2)
        )
        
        outputs.citations = {c.line: c.source for c in self.citations}
        
        return outputs


if __name__ == "__main__":
    from src.core.types import FilingStatus
    
    print("Testing Schedule SE Agent...")
    print("=" * 80)
    
    # Test case 1: Moderate self-employment income
    inputs1 = ScheduleSEInputs(
        net_profit_loss=50000,
        filing_status=FilingStatus.SINGLE
    )
    
    agent = ScheduleSEAgent()
    outputs1 = agent.process(inputs1)
    
    print("\nTest Case 1: Net Profit $50,000")
    print("-" * 80)
    print(f"Net Earnings (Line 4):               ${outputs1.net_earnings:>12,.2f}")
    print(f"Self-Employment Tax (Line 12):       ${outputs1.self_employment_tax:>12,.2f}")
    print(f"Deduction (Line 13):                 ${outputs1.deduction:>12,.2f}")
    
    # Test case 2: High self-employment income (above SS wage base)
    inputs2 = ScheduleSEInputs(
        net_profit_loss=200000,
        filing_status=FilingStatus.SINGLE
    )
    
    outputs2 = agent.process(inputs2)
    
    print("\nTest Case 2: Net Profit $200,000 (above SS wage base)")
    print("-" * 80)
    print(f"Net Earnings (Line 4):               ${outputs2.net_earnings:>12,.2f}")
    print(f"Self-Employment Tax (Line 12):       ${outputs2.self_employment_tax:>12,.2f}")
    print(f"Deduction (Line 13):                 ${outputs2.deduction:>12,.2f}")
    
    # Test case 3: Below $400 threshold
    inputs3 = ScheduleSEInputs(
        net_profit_loss=300,
        filing_status=FilingStatus.SINGLE
    )
    
    outputs3 = agent.process(inputs3)
    
    print("\nTest Case 3: Net Profit $300 (below $400 threshold)")
    print("-" * 80)
    print(f"Net Earnings (Line 4):               ${outputs3.net_earnings:>12,.2f}")
    print(f"Self-Employment Tax (Line 12):       ${outputs3.self_employment_tax:>12,.2f}")
    print(f"Deduction (Line 13):                 ${outputs3.deduction:>12,.2f}")
    
    print("\nCitations (Test Case 1):")
    print("-" * 80)
    agent_test = ScheduleSEAgent()
    agent_test.process(inputs1)
    for citation in agent_test.citations:
        print(f"{citation.line}: {citation.reasoning}")
