# Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Set Up Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your API key (use any ONE of these)
# For OpenAI:
OPENAI_API_KEY=sk-your-key-here

# OR for Anthropic:
ANTHROPIC_API_KEY=your-key-here

# OR for Google:
GOOGLE_API_KEY=your-key-here
```

### Step 3: Run a Test Case

```bash
# Run the simplest test case (single filer with W-2)
python main.py --case single-w2 --verbose
```

**Expected Output:**
```
================================================================================
Processing Tax Return
================================================================================

[4/4] Processing Form 1040 (Main Tax Return)...

  AGI: $50,000.00
  Taxable Income: $35,400.00
  Tax: $4,027.00
  Total Tax: $4,027.00
  Payments: $5,000.00
  REFUND: $973.00

================================================================================
FORM 1040 - U.S. INDIVIDUAL INCOME TAX RETURN
================================================================================

Line 1z  - Wages:                           $50,000.00
Line 11  - AGI:                             $50,000.00
Line 12  - Deductions:                      $14,600.00
Line 15  - Taxable Income:                  $35,400.00
Line 16  - Tax:                              $4,027.00
Line 24  - Total Tax:                        $4,027.00
Line 33  - Total Payments:                   $5,000.00
--------------------------------------------------------------------------------
Line 34  - REFUND:                             $973.00 ✓
================================================================================
```

---

## 📋 Test Cases Available

### 1. single-w2 (HelloWorld)
```bash
python main.py --case single-w2 --verify --verbose  
```
**What it tests:**
- Single filing status
- W-2 wages only
- Standard deduction
- Basic Form 1040

### 2. mfj-w2 (Married Filing Jointly)
```bash
python main.py --case mfj-w2 --verify --verbose
```
**What it tests:**
- Married filing jointly status
- Higher standard deduction
- Joint return logic

### 3. single-w2-1099int (Interest Income)
```bash
python main.py --case single-w2-1099int --verify --verbose
```
**What it tests:**
- W-2 wages
- Interest income (Schedule B)
- Form integration

---

## 🧪 Testing Individual Components

### Test Tax Table
```bash
python src/tools/tax_table.py
```

### Test Standard Deduction
```bash
python src/tools/standard_deduction.py
```

### Test Form 1040 Agent
```bash
python src/agents/form_1040_agent.py
```

### Test Schedule B Agent
```bash
python src/agents/schedule_b_agent.py
```

### Test PDF Navigator
```bash
python src/tools/pdf_navigator.py
```

### Test Arithmetic Verifier
```bash
python src/verifiers/arithmetic_verifier.py
```

---

## 📝 Creating Custom Test Cases

Create a JSON file with this structure:

```json
{
  "filing_status": "single",
  "taxpayer_name": "John Doe",
  "ssn": "123-45-6789",
  "age": 35,
  "w2": [
    {
      "wages": 75000,
      "federal_withholding": 8000
    }
  ],
  "income_1099_int": [
    {
      "payer": "Chase Bank",
      "interest_income": 250
    }
  ]
}
```

Save as `my_test.json` and run:

```bash
python main.py --input my_test.json --verify --verbose
```

---

## 🔍 Understanding the Output

### Key Lines Explained

| Line | Description | Example |
|------|-------------|---------|
| **Line 1z** | Total wages from W-2(s) | $50,000 |
| **Line 9** | Total income (wages + interest + dividends + other) | $50,000 |
| **Line 10** | Adjustments to income (student loan interest, etc.) | $0 |
| **Line 11** | **Adjusted Gross Income (AGI)** | $50,000 |
| **Line 12** | Standard or itemized deduction | $14,600 |
| **Line 15** | **Taxable Income** (AGI - deductions) | $35,400 |
| **Line 16** | **Tax** (from tax table) | $4,027 |
| **Line 19** | Child tax credit | $0 |
| **Line 24** | **Total Tax** (tax - credits + other taxes) | $4,027 |
| **Line 33** | Total payments (withholding + estimated tax) | $5,000 |
| **Line 34** | **REFUND** (if payments > tax) | $973 ✓ |
| **Line 37** | Amount owed (if tax > payments) | $0 |

---

## 🛠️ Troubleshooting

### Issue: "OPENAI_API_KEY not found"

**Solution:**
```bash
# Make sure .env file exists
cp .env.example .env

# Edit .env and add your API key
nano .env  # or use any text editor
```

### Issue: "PDF not found"

**Solution:**

The system works without PDFs, but for best results:

1. Download IRS forms from https://www.irs.gov/forms-instructions
2. Place in `data/irs_forms/` directory
3. Name format: `i1040-2024.pdf` (instructions), `f1040-2024.pdf` (form)

**Forms to download:**
- `i1040-2024.pdf` - Form 1040 Instructions
- `i1040sb-2024.pdf` - Schedule B Instructions
- `i1040sc-2024.pdf` - Schedule C Instructions
- `i1040sse-2024.pdf` - Schedule SE Instructions

### Issue: Module not found errors

**Solution:**
```bash
# Make sure you're in the Assignment directory
cd c:/Users/user/Desktop/Assignment

# Reinstall dependencies
pip install -r requirements.txt

# Run from project root
python main.py --case single-w2
```

### Issue: Different results on repeated runs

**Cause:** LLM temperature > 0 causes variation

**Solution:**
```bash
# Set temperature to 0 in .env
LLM_TEMPERATURE=0.0
```

---

## 📚 Next Steps

1. **Read the Architecture**: Check `docs/DESIGN_DECISIONS.md`
2. **Experiment**: Try modifying wages in test cases
3. **Add Forms**: Implement Schedule D or Schedule A
4. **Improve Verifiers**: Add logic or cross-form verifiers
5. **Optimize**: Add caching for LLM calls

---

## 💡 Pro Tips

### Speed Up Development

```bash
# Test deterministic tools first (no API calls)
python src/tools/tax_table.py
python src/tools/standard_deduction.py

# Then test agents
python src/agents/form_1040_agent.py
```

### Save API Costs

```bash
# Use temperature=0 for consistency
# Cache LLM responses (future enhancement)
# Test with small cases first
```

### Debug Issues

```bash
# Use verbose mode
python main.py --case single-w2 --verbose

# Check citations
# Look for warnings in output
```

---

## 🎯 Success Criteria

You'll know it's working when:

1. ✅ **No errors** in verbose output
2. ✅ **Refund/tax owed** matches expected
3. ✅ **Verifier passes** (if using --verify)
4. ✅ **Citations** are present for key lines

Example successful run:
```
[4/4] Processing Form 1040 (Main Tax Return)...
  AGI: $50,000.00
  Taxable Income: $35,400.00
  Tax: $4,027.00
  Total Tax: $4,027.00
  Payments: $5,000.00
  REFUND: $973.00

================================================================================
Running Verifiers
================================================================================

Arithmetic Verifier:
  Status: ✓ PASS
  Errors: 0
  Warnings: 0

✓ All verifications passed!
```

---

## 🆘 Getting Help

- **Review README.md** for architecture overview
- **Check DESIGN_DECISIONS.md** for implementation details
- **Examine test outputs** in verbose mode
- **Review source code** - it's well-commented!

---

**Happy Tax Preparing! 📊**
