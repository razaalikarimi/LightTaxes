"""
Type definitions for the tax agent system.
Defines typed inputs/outputs for all forms following codebase-style architecture.
"""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field
from enum import Enum


class FilingStatus(str, Enum):
    """IRS Filing Status"""
    SINGLE = "single"
    MARRIED_FILING_JOINTLY = "married_filing_jointly"
    MARRIED_FILING_SEPARATELY = "married_filing_separately"
    HEAD_OF_HOUSEHOLD = "head_of_household"
    QUALIFYING_WIDOW = "qualifying_widow"


class W2(BaseModel):
    """W-2 Wage and Tax Statement"""
    employer: Optional[str] = None
    wages: float = Field(..., description="Box 1 - Wages, tips, other compensation")
    federal_withholding: float = Field(0.0, description="Box 2 - Federal income tax withheld")
    social_security_wages: Optional[float] = None
    medicare_wages: Optional[float] = None
    
    
class Form1099INT(BaseModel):
    """1099-INT Interest Income"""
    payer: Optional[str] = None
    interest_income: float = Field(..., description="Box 1 - Interest income")
    

class Form1099DIV(BaseModel):
    """1099-DIV Dividend Income"""
    payer: Optional[str] = None
    ordinary_dividends: float = Field(0.0, description="Box 1a - Ordinary dividends")
    qualified_dividends: float = Field(0.0, description="Box 1b - Qualified dividends")


class BusinessIncome(BaseModel):
    """Schedule C - Business Income"""
    business_name: Optional[str] = None
    gross_receipts: float = 0.0
    returns_allowances: float = 0.0
    cost_of_goods_sold: float = 0.0
    other_income: float = 0.0
    advertising: float = 0.0
    car_truck_expenses: float = 0.0
    commissions_fees: float = 0.0
    contract_labor: float = 0.0
    depreciation: float = 0.0
    insurance: float = 0.0
    interest: float = 0.0
    legal_professional: float = 0.0
    office_expense: float = 0.0
    rent_lease: float = 0.0
    repairs_maintenance: float = 0.0
    supplies: float = 0.0
    taxes_licenses: float = 0.0
    travel: float = 0.0
    meals: float = 0.0
    utilities: float = 0.0
    wages: float = 0.0
    other_expenses: Dict[str, float] = Field(default_factory=dict)


class Dependent(BaseModel):
    """Dependent information"""
    name: str
    ssn: str
    relationship: str
    qualifying_child: bool = False
    credit_for_other_dependents: bool = False


class TaxpayerInfo(BaseModel):
    """Taxpayer personal information"""
    name: str
    ssn: str
    dob: Optional[str] = None
    age: Optional[int] = None
    blind: bool = False
    spouse_name: Optional[str] = None
    spouse_ssn: Optional[str] = None
    spouse_dob: Optional[str] = None
    spouse_age: Optional[int] = None
    spouse_blind: bool = False


# ============================================================================
# FORM INPUT TYPES (Following the codebase-style typed module pattern)
# ============================================================================

class TaxInputs(BaseModel):
    """Main input data structure - maps to input.json from TaxCalcBench"""
    filing_status: FilingStatus
    taxpayer: TaxpayerInfo
    dependents: List[Dependent] = Field(default_factory=list)
    w2: List[W2] = Field(default_factory=list)
    income_1099_int: List[Form1099INT] = Field(default_factory=list)
    income_1099_div: List[Form1099DIV] = Field(default_factory=list)
    business_income: Optional[BusinessIncome] = None
    

class ScheduleBInputs(BaseModel):
    """Schedule B - Interest and Ordinary Dividends"""
    interest_income: List[Form1099INT] = Field(default_factory=list)
    dividend_income: List[Form1099DIV] = Field(default_factory=list)


class ScheduleCInputs(BaseModel):
    """Schedule C - Profit or Loss from Business"""
    business: BusinessIncome
    filing_status: FilingStatus


class ScheduleSEInputs(BaseModel):
    """Schedule SE - Self-Employment Tax"""
    net_profit_loss: float  # From Schedule C
    filing_status: FilingStatus


class Schedule1Inputs(BaseModel):
    """Schedule 1 - Additional Income and Adjustments to Income"""
    taxable_refunds: float = 0.0
    alimony_received: float = 0.0
    business_income: float = 0.0  # From Schedule C
    capital_gain_loss: float = 0.0
    other_income: float = 0.0
    # Adjustments
    educator_expenses: float = 0.0
    business_expenses: float = 0.0
    health_savings_deduction: float = 0.0
    self_employment_tax_deduction: float = 0.0  # 1/2 of SE tax
    self_employed_retirement: float = 0.0
    self_employed_health_insurance: float = 0.0
    student_loan_interest: float = 0.0


class Form1040Inputs(BaseModel):
    """Form 1040 - U.S. Individual Income Tax Return"""
    filing_status: FilingStatus
    taxpayer: TaxpayerInfo
    dependents: List[Dependent] = Field(default_factory=list)
    # Income (Lines 1-8)
    wages: float = 0.0  # Line 1 (from W-2)
    interest: float = 0.0  # Line 2b (from Schedule B)
    dividends: float = 0.0  # Line 3b (from Schedule B) 
    # Additional income from Schedule 1
    schedule_1_additional_income: float = 0.0  # Line 8
    # Adjustments from Schedule 1
    schedule_1_adjustments: float = 0.0  # Line 10


class Schedule8812Inputs(BaseModel):
    """Schedule 8812 - Child Tax Credit"""
    dependents: List[Dependent]
    agi: float
    tax_before_credits: float
    filing_status: FilingStatus


# ============================================================================
# FORM OUTPUT TYPES
# ============================================================================

class ScheduleBOutputs(BaseModel):
    """Schedule B Outputs"""
    total_interest: float  # Line 4
    total_dividends: float  # Line 6
    citations: Dict[str, str] = Field(default_factory=dict)


class ScheduleCOutputs(BaseModel):
    """Schedule C Outputs"""
    gross_income: float  # Line 7
    total_expenses: float  # Line 28
    net_profit_loss: float  # Line 31
    citations: Dict[str, str] = Field(default_factory=dict)


class ScheduleSEOutputs(BaseModel):
    """Schedule SE Outputs"""
    net_earnings: float  # Line 4
    self_employment_tax: float  # Line 12
    deduction: float  # Line 13 (1/2 of SE tax)
    citations: Dict[str, str] = Field(default_factory=dict)


class Schedule1Outputs(BaseModel):
    """Schedule 1 Outputs"""
    total_additional_income: float  # Line 10
    total_adjustments: float  # Line 26
    citations: Dict[str, str] = Field(default_factory=dict)


class Form1040Outputs(BaseModel):
    """Form 1040 Outputs - matches TaxCalcBench output.xml structure"""
    # Income
    line_1z: float = 0.0  # Total wages
    line_2b: float = 0.0  # Taxable interest
    line_3b: float = 0.0  # Qualified dividends
    line_8: float = 0.0  # Additional income from Schedule 1
    line_9: float = 0.0  # Total income
    line_10: float = 0.0  # Adjustments to income
    line_11: float = 0.0  # Adjusted Gross Income (AGI)
    
    # Deductions
    line_12: float = 0.0  # Standard/Itemized deduction
    line_15: float = 0.0  # Taxable income
    
    # Tax and Credits
    line_16: float = 0.0  # Tax (from tax table)
    line_19: float = 0.0  # Child tax credit
    line_22: float = 0.0  # Total other taxes
    line_23: float = 0.0  # Self-employment tax
    line_24: float = 0.0  # Total tax
    
    # Payments
    line_25a: float = 0.0  # Federal income tax withheld (Form W-2)
    line_33: float = 0.0  # Total payments
    
    # Refund or Amount Owed
    line_34: float = 0.0  # Overpayment (refund)
    line_37: float = 0.0  # Amount you owe
    
    citations: Dict[str, str] = Field(default_factory=dict)


class Schedule8812Outputs(BaseModel):
    """Schedule 8812 Outputs"""
    child_tax_credit: float
    additional_child_tax_credit: float = 0.0
    citations: Dict[str, str] = Field(default_factory=dict)


# ============================================================================
# VERIFICATION TYPES
# ============================================================================

class VerificationError(BaseModel):
    """Error found by a verifier"""
    form: str
    line: str
    error_type: str
    message: str
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    severity: Literal["warning", "error", "critical"] = "error"


class VerificationResult(BaseModel):
    """Result from a verifier"""
    verifier_name: str
    passed: bool
    errors: List[VerificationError] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# ============================================================================
# AGENT TYPES
# ============================================================================

class Citation(BaseModel):
    """IRS citation for a decision"""
    form: str
    line: str
    source: str  # e.g., "IRS Form 1040 Instructions, Page 25, Line 11"
    reasoning: str


class AgentResponse(BaseModel):
    """Response from any form agent"""
    form_name: str
    outputs: Any  # Will be specific FormOutputs type
    citations: List[Citation] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
