"""
Arithmetic Verifier - Validates mathematical correctness across forms
Part of the verifier swarm architecture from the paper
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from typing import List
from src.core.types import VerificationResult, VerificationError, Form1040Outputs


class ArithmeticVerifier:
    """
    Verifies arithmetic correctness in tax returns.
    Checks:
    - Additions/subtractions are correct
    - Non-negative amounts where required
    - Consistency across related fields
    """
    
    def __init__(self):
        self.name = "Arithmetic Verifier"
    
    def verify_form_1040(self, outputs: Form1040Outputs) -> VerificationResult:
        """
        Verify Form 1040 arithmetic
        
        Args:
            outputs: Form 1040 outputs to verify
            
        Returns:
            VerificationResult with any errors found
        """
        errors: List[VerificationError] = []
        warnings: List[str] = []
        
        # Verify Line 9: Total Income
        expected_line_9 = (
            outputs.line_1z +
            outputs.line_2b +
            outputs.line_3b +
            outputs.line_8
        )
        
        if abs(outputs.line_9 - expected_line_9) > 0.01:  # Allow for rounding
            errors.append(VerificationError(
                form="1040",
                line="Line 9",
                error_type="arithmetic",
                message="Total income calculation incorrect",
                expected=expected_line_9,
                actual=outputs.line_9,
                severity="error"
            ))
        
        # Verify Line 11: AGI
        expected_line_11 = outputs.line_9 - outputs.line_10
        
        if abs(outputs.line_11 - expected_line_11) > 0.01:
            errors.append(VerificationError(
                form="1040",
                line="Line 11",
                error_type="arithmetic",
                message="AGI calculation incorrect",
                expected=expected_line_11,
                actual=outputs.line_11,
                severity="error"
            ))
        
        # Verify Line 15: Taxable Income
        expected_line_15 = max(0, outputs.line_11 - outputs.line_12)
        
        if abs(outputs.line_15 - expected_line_15) > 0.01:
            errors.append(VerificationError(
                form="1040",
                line="Line 15",
                error_type="arithmetic",
                message="Taxable income calculation incorrect",
                expected=expected_line_15,
                actual=outputs.line_15,
                severity="error"
            ))
        
        # Verify Line 15 is non-negative
        if outputs.line_15 < 0:
            errors.append(VerificationError(
                form="1040",
                line="Line 15",
                error_type="logic",
                message="Taxable income cannot be negative",
                expected=0,
                actual=outputs.line_15,
                severity="critical"
            ))
        
        # Verify Line 24: Total Tax
        expected_line_24 = outputs.line_16 - outputs.line_19 + outputs.line_23
        
        if abs(outputs.line_24 - expected_line_24) > 0.01:
            errors.append(VerificationError(
                form="1040",
                line="Line 24",
                error_type="arithmetic",
                message="Total tax calculation incorrect",
                expected=expected_line_24,
                actual=outputs.line_24,
                severity="error"
            ))
        
        # Verify refund or amount owed logic
        if outputs.line_33 > outputs.line_24:
            # Should be refund
            expected_refund = outputs.line_33 - outputs.line_24
            
            if abs(outputs.line_34 - expected_refund) > 0.01:
                errors.append(VerificationError(
                    form="1040",
                    line="Line 34",
                    error_type="arithmetic",
                    message="Refund calculation incorrect",
                    expected=expected_refund,
                    actual=outputs.line_34,
                    severity="error"
                ))
            
            if outputs.line_37 != 0:
                errors.append(VerificationError(
                    form="1040",
                    line="Line 37",
                    error_type="logic",
                    message="Line 37 should be 0 when there is a refund",
                    expected=0,
                    actual=outputs.line_37,
                    severity="error"
                ))
        else:
            # Should owe
            expected_owed = outputs.line_24 - outputs.line_33
            
            if abs(outputs.line_37 - expected_owed) > 0.01:
                errors.append(VerificationError(
                    form="1040",
                    line="Line 37",
                    error_type="arithmetic",
                    message="Amount owed calculation incorrect",
                    expected=expected_owed,
                    actual=outputs.line_37,
                    severity="error"
                ))
            
            if outputs.line_34 != 0:
                errors.append(VerificationError(
                    form="1040",
                    line="Line 34",
                    error_type="logic",
                    message="Line 34 should be 0 when tax is owed",
                    expected=0,
                    actual=outputs.line_34,
                    severity="error"
                ))
        
        # Warnings for unusual values
        if outputs.line_11 > 1000000:
            warnings.append(f"High AGI: ${outputs.line_11:,.2f} - verify accuracy")
        
        if outputs.line_16 == 0 and outputs.line_15 > 0:
            warnings.append("Tax is $0 despite positive taxable income - verify")
        
        return VerificationResult(
            verifier_name=self.name,
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


if __name__ == "__main__":
    from src.core.types import Form1040Outputs
    
    print("Testing Arithmetic Verifier...")
    print("=" * 80)
    
    # Test Case 1: Correct calculations
    outputs1 = Form1040Outputs(
        line_1z=50000,
        line_2b=0,
        line_3b=0,
        line_8=0,
        line_9=50000,
        line_10=0,
        line_11=50000,
        line_12=14600,
        line_15=35400,
        line_16=4027,
        line_19=0,
        line_23=0,
        line_24=4027,
        line_25a=5000,
        line_33=5000,
        line_34=973,
        line_37=0
    )
    
    verifier = ArithmeticVerifier()
    result1 = verifier.verify_form_1040(outputs1)
    
    print("\nTest Case 1: Correct Calculations")
    print("-" * 80)
    print(f"Passed: {result1.passed}")
    print(f"Errors: {len(result1.errors)}")
    print(f"Warnings: {len(result1.warnings)}")
    
    if result1.errors:
        for error in result1.errors:
            print(f"  ERROR: {error.line} - {error.message}")
    
    # Test Case 2: Incorrect calculations
    outputs2 = Form1040Outputs(
        line_1z=50000,
        line_2b=500,
        line_3b=0,
        line_8=0,
        line_9=50000,  # WRONG: Should be 50500
        line_10=0,
        line_11=50000,  # WRONG: Cascades from Line 9
        line_12=14600,
        line_15=35000,  # WRONG
        line_16=4027,
        line_19=0,
        line_23=0,
        line_24=4027,
        line_25a=5000,
        line_33=5000,
        line_34=973,
        line_37=0
    )
    
    result2 = verifier.verify_form_1040(outputs2)
    
    print("\nTest Case 2: Incorrect Calculations")
    print("-" * 80)
    print(f"Passed: {result2.passed}")
    print(f"Errors: {len(result2.errors)}")
    
    if result2.errors:
        print("\nDetected Errors:")
        for error in result2.errors:
            print(f"  {error.line}: {error.message}")
            print(f"    Expected: ${error.expected:,.2f}, Got: ${error.actual:,.2f}")
