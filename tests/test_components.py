"""
Simple test runner to verify all components work
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_tax_table():
    """Test tax table calculations"""
    from src.tools.tax_table import calculate_tax
    
    print("Testing Tax Table...")
    
    # Test case from TaxCalcBench: single-w2
    # Taxable income: $35,400, Filing: Single
    # Expected tax: ~$4,016-4,027
    
    tax = calculate_tax(35400, "single")
    print(f"  Taxable Income: $35,400")
    print(f"  Tax: ${tax:,.2f}")
    
    assert 4000 < tax < 4100, f"Tax ${tax} out of expected range"
    print("  ✓ PASS\n")


def test_standard_deduction():
    """Test standard deduction"""
    from src.tools.standard_deduction import get_standard_deduction
    
    print("Testing Standard Deduction...")
    
    # Single filer, 2024
    deduction = get_standard_deduction("single")
    print(f"  Single filer: ${deduction:,.2f}")
    assert deduction == 14600, f"Expected $14,600, got ${deduction}"
    
    # MFJ, 2024
    deduction = get_standard_deduction("married_filing_jointly")
    print(f"  MFJ: ${deduction:,.2f}")
    assert deduction == 29200, f"Expected $29,200, got ${deduction}"
    
    print("  ✓ PASS\n")


def test_form_1040_agent():
    """Test Form 1040 agent"""
    from src.agents.form_1040_agent import Form1040Agent
    from src.core.types import Form1040Inputs, TaxpayerInfo, FilingStatus
    
    print("Testing Form 1040 Agent...")
    
    # Simple case: single, $50k wages, $5k withholding
    taxpayer = TaxpayerInfo(
        name="Test User",
        ssn="000-00-0000",
        age=35
    )
    
    inputs = Form1040Inputs(
        filing_status=FilingStatus.SINGLE,
        taxpayer=taxpayer,
        wages=50000,
        interest=0,
        dividends=0,
        schedule_1_additional_income=0,
        schedule_1_adjustments=0
    )
    
    agent = Form1040Agent(enable_citations=False)
    outputs = agent.process(inputs)
    
    print(f"  Wages: ${outputs.line_1z:,.2f}")
    print(f"  AGI: ${outputs.line_11:,.2f}")
    print(f"  Taxable Income: ${outputs.line_15:,.2f}")
    print(f"  Tax: ${outputs.line_16:,.2f}")
    
    # Verify calculations
    assert outputs.line_1z == 50000
    assert outputs.line_11 == 50000  # No adjustments
    assert outputs.line_12 == 14600  # Standard deduction
    assert outputs.line_15 == 35400  # 50000 - 14600
    assert 4000 < outputs.line_16 < 4100  # Tax on 35400
    
    print("  ✓ PASS\n")


def test_arithmetic_verifier():
    """Test arithmetic verifier"""
    from src.verifiers.arithmetic_verifier import ArithmeticVerifier
    from src.core.types import Form1040Outputs
    
    print("Testing Arithmetic Verifier...")
    
    # Correct calculations
    outputs = Form1040Outputs(
        line_1z=50000,
        line_9=50000,
        line_11=50000,
        line_12=14600,
        line_15=35400,
        line_16=4027,
        line_24=4027,
        line_33=5000,
        line_34=973,
        line_37=0
    )
    
    verifier = ArithmeticVerifier()
    result = verifier.verify_form_1040(outputs)
    
    print(f"  Passed: {result.passed}")
    print(f"  Errors: {len(result.errors)}")
    
    assert result.passed, "Verifier should pass correct calculations"
    assert len(result.errors) == 0
    
    print("  ✓ PASS\n")


def run_all_tests():
    """Run all component tests"""
    print("=" * 80)
    print("RUNNING COMPONENT TESTS")
    print("=" * 80)
    print()
    
    try:
        test_tax_table()
        test_standard_deduction()
        test_form_1040_agent()
        test_arithmetic_verifier()
        
        print("=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        return True
        
    except AssertionError as e:
        print("\n" + "=" * 80)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 80)
        return False
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ ERROR: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
