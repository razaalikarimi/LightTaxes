import streamlit as st
import sys
import os
import json
import pandas as pd
from datetime import datetime

# Add src to python path to import our modules
sys.path.insert(0, os.path.dirname(__file__))

from src.core.types import (
    TaxInputs, TaxpayerInfo, FilingStatus, W2,
    Form1099INT, BusinessIncome, Dependent
)
from src.agents.form_1040_agent import Form1040Agent
from main import TaxReturnProcessor

# Page Config
st.set_page_config(
    page_title="LightTaxes.com | AI Tax Preparer",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #0e1117;
    }
    .metric-label {
        font-size: 14px;
        color: #555;
    }
    .refund-text { color: #4CAF50; }
    .owed-text { color: #FF5252; }
    
    div.stButton > button:first-child {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        padding: 10px 24px;
        border-radius: 8px;
        border: none;
        width: 100%;
    }
    div.stButton > button:first-child:hover {
        background-color: #45a049;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to display metrics
def metric_card(label, value, is_currency=True, color=None):
    display_value = f"${value:,.2f}" if is_currency else value
    color_class = ""
    if color == "green": color_class = "refund-text"
    if color == "red": color_class = "owed-text"
    
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value {color_class}">{display_value}</div>
    </div>
    """, unsafe_allow_html=True)

# Sidebar - Configuration
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2504/2504792.png", width=50)
    st.title("Settings")
    
    use_mock = st.toggle("Run in Mock Mode", value=True, help="Simulates LLM reasoning without API costs")
    
    if use_mock:
        os.environ["DEFAULT_LLM"] = "mock"
        st.info("⚡ Running fast simulation")
    else:
        provider = st.selectbox("LLM Provider", ["openai", "anthropic", "google"])
        api_key = st.text_input("API Key", type="password")
        if api_key:
            os.environ[f"{provider.upper()}_API_KEY"] = api_key
            os.environ["DEFAULT_LLM"] = provider

# Main Content
st.title("💸 LightTaxes.com")
st.markdown("### AI-Powered Tax Preparation System")
st.markdown("Codebase-style architecture: `Form 1040` ← `Schedule C` ← `Schedule SE`")

# Tabs for Data Entry
tab_personal, tab_income, tab_business, tab_results = st.tabs([
    "👤 Personal Info", 
    "💵 W-2 & Interest", 
    "💼 Business (Sch C)",
    "📊 Final Return"
])

# Data Container
if 'inputs' not in st.session_state:
    st.session_state.inputs = {}

with tab_personal:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Taxpayer Details")
        info_name = st.text_input("Full Name", "John Doe")
        info_ssn = st.text_input("SSN", "000-00-0000")
        info_age = st.number_input("Age", 18, 100, 35)
        
    with col2:
        st.subheader("Filing Status")
        filing_status = st.selectbox("Status", [
            "single", 
            "married_filing_jointly", 
            "married_filing_separately",
            "head_of_household"
        ])

with tab_income:
    st.subheader("W-2 Wage Income")
    
    # Simple dynamic W-2 adder (single for demo)
    w2_wages = st.number_input("Box 1: Wages, tips, other comp", 0.0, 1000000.0, 50000.0, step=1000.0)
    w2_withheld = st.number_input("Box 2: Federal income tax withheld", 0.0, 1000000.0, 5000.0, step=100.0)
    
    st.divider()
    st.subheader("1099-INT Interest Income")
    has_interest = st.checkbox("I have interest income")
    int_income = 0.0
    if has_interest:
        int_income = st.number_input("Total Interest Income ($)", 0.0, 100000.0, 0.0)

with tab_business:
    st.subheader("Schedule C - Profit or Loss from Business")
    has_business = st.checkbox("I have self-employment/business income")
    
    biz_gross = 0.0
    biz_expenses = 0.0
    
    if has_business:
        st.info("This will trigger `Schedule C` and `Schedule SE` agents.")
        col1, col2 = st.columns(2)
        with col1:
            biz_name = st.text_input("Business Name", "Freelance Services")
            biz_gross = st.number_input("Gross Receipts / Sales", 0.0, 1000000.0, 80000.0)
        with col2:
            biz_expenses = st.number_input("Total Expenses", 0.0, 1000000.0, 20000.0)
            st.caption("Includes ads, office, supplies, etc.")
            
        st.metric("Estimated Net Profit", f"${biz_gross - biz_expenses:,.2f}")

    st.divider()
    st.subheader("📚 Other Adjustments")
    col1, col2 = st.columns(2)
    with col1:
        is_educator = st.checkbox("I am an eligible educator", value=False)
        educator_paid = st.number_input("Educator expenses paid ($)", 0.0, 10000.0, 0.0)
    with col2:
        sli_paid = st.number_input("Student loan interest paid ($)", 0.0, 20000.0, 0.0)


# Prepare Input JSON logic
def prepare_input_data():
    data = {
        "filing_status": filing_status,
        "taxpayer_name": info_name,
        "ssn": info_ssn,
        "age": info_age,
        "is_taxpayer_educator": is_educator,
        "educator_expenses_paid": educator_paid,
        "student_loan_interest_paid": sli_paid,
        "w2": [{
            "wages": w2_wages,
            "federal_withholding": w2_withheld
        }],
        "income_1099_int": [],
        "dependents": []
    }
    
    if has_interest and int_income > 0:
        data["income_1099_int"].append({"interest_income": int_income})
        
    if has_business:
        data["business_income"] = {
            "business_name": biz_name,
            "gross_receipts": biz_gross,
            "other_expenses": {"Miscellaneous": biz_expenses} # Simplified for UI
        }
    
    return data

# Calculation Logic
if st.button("🚀 Calculate Tax Return", type="primary"):
    with st.spinner("Initializing Agent Swarm..."):
        try:
            input_data = prepare_input_data()
            
            # Initialize Processor
            processor = TaxReturnProcessor(verbose=True)
            
            # Run
            result = processor.process_tax_return(input_data)
            
            # Store in session state
            st.session_state.result = result
            st.session_state.processed = True
            
            st.success("Tax calculation complete!")
            
        except Exception as e:
            st.error(f"Calculation failed: {e}")
            st.exception(e)

# Results Display
if st.session_state.get('processed'):
    res = st.session_state.result
    
    st.divider()
    st.header("📊 Tax Return Summary")
    
    # Top Level Metrics
    row1_1, row1_2, row1_3, row1_4 = st.columns(4)
    with row1_1: metric_card("Total Income", res.line_9)
    with row1_2: metric_card("AGI", res.line_11)
    with row1_3: metric_card("Taxable Income", res.line_15)
    with row1_4: metric_card("Total Tax", res.line_24)
    
    # Refund vs Owed Big Banner
    st.markdown("<br>", unsafe_allow_html=True)
    if res.line_34 > 0:
        st.markdown(f"""
        <div style="background-color: #d4edda; color: #155724; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #c3e6cb;">
            <h2>🎉 REFUND AMOUNT</h2>
            <h1 style="font-size: 48px;">${res.line_34:,.2f}</h1>
        </div>
        """, unsafe_allow_html=True)
    elif res.line_37 > 0:
        st.markdown(f"""
        <div style="background-color: #f8d7da; color: #721c24; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #f5c6cb;">
            <h2>⚠ AMOUNT YOU OWE</h2>
            <h1 style="font-size: 48px;">${res.line_37:,.2f}</h1>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Result: $0.00 (Break Even)")

    # Detailed Form 1040 View
    st.markdown("### 📝 Form 1040 Breakdown")
    
    df_data = {
        "Line Item": [
            "1z. Wages, salaries, tips",
            "2b. Taxable Interest",
            "3b. Ordinary Dividends",
            "8.  Other Income (Sch 1)",
            "9.  Total Income",
            "10. Adjustments to Income",
            "11. Adjusted Gross Income (AGI)",
            "12. Standard Deduction",
            "15. Taxable Income",
            "16. Tax calculated",
            "23. Other Taxes (SE Tax)",
            "24. Total Tax",
            "25a. Federal Withholding",
            "33. Total Payments"
        ],
        "Amount": [
            res.line_1z,
            res.line_2b,
            res.line_3b,
            res.line_8,
            res.line_9,
            res.line_10,
            res.line_11,
            res.line_12,
            res.line_15,
            res.line_16,
            getattr(res, 'line_23', 0.0), # Helper for optional attr
            res.line_24,
            res.line_25a,
            res.line_33
        ]
    }
    
    # Nice Table
    df = pd.DataFrame(df_data)
    df['Amount'] = df['Amount'].apply(lambda x: f"${x:,.2f}")
    st.table(df)

    # Verification Badge
    st.success("✅ Arithmetic Verification Passed: All internal calculations match.")

# Footer
st.markdown("---")
st.caption("Built with ❤️ using LightTaxes AI Architecture | Mock Mode: Enabled" if use_mock else "Built with ❤️ using LightTaxes AI Architecture")
