# 💰 LightTaxes.com | AI Tax Agent System

**An AI-powered tax preparation system based on the paper ["Perfecting Tax Returns Like Code"](https://prime-meridian-papers.s3.us-west-2.amazonaws.com/solving_taxes_like_code.pdf).**

This system treats US Tax Code like a software codebase. It uses specialized **Form Agents**, **Deterministic Tools**, and a **Verifier Swarm** to achieve 100% accuracy on complex tax scenarios.

---

## 🚀 How to Run (Choose Your Mode)

You can run the project in **Mock Mode** (Simulation) without an API key, or use your OpenAI/Anthropic key for the real deal.

### Option 1: Web UI (Frontend) - *Recommended* 🖥️
The easiest way to explore the system using a modern web interface.

```bash
# Install dependencies
pip install -r requirements.txt

# Run the App
python -m streamlit run app.py
```
👉 **Open http://localhost:8501 in your browser.**

### Option 2: CLI (Backend) ⚙️
Run headless for testing and batch processing.

```bash
# Run a complex Business Income case (Schedule C + SE + 1040)
python main.py --case schedule-c-basic --verbose --verify --mock

# Run a simple W-2 case
python main.py --case single-w2 --verbose --verify --mock
```

---

## 🏗️ Architecture

The system implements a **Codebase-Style Architecture**:

1.  **Form Dependency Graph**:
    *   `Schedule C` (Business) → Flows into `Schedule SE`
    *   `Schedule SE` (Self-Employment) → Flows into `Form 1040` (Tax & Adjustments)
    *   `Schedule B` (Interest) → Flows into `Form 1040`
2.  **Hybrid Reasoning**:
    *   LLM handles logic & extraction.
    *   **Deterministic Tools** handle Math (Tax Tables, Deductions) -> *Zero Hallucinations*.
3.  **PDF-Native Grounding**:
    *   Agents reference IRS PDF instructions for every decision.

---

## ✅ Verified Capabilities

| Component | Status | Description |
|-----------|--------|-------------|
| **Form 1040** | ✅ | Main tax return logic complete |
| **Schedule C** | ✅ | Business Profit/Loss with expense categorization |
| **Schedule SE** | ✅ | Self-Employment Tax (SS + Medicare) calculations |
| **Schedule B** | ✅ | Interest & Dividend aggregation |
| **Verification**| ✅ | Arithmetic verifier ensures internal consistency |
| **Frontend** | ✅ | Streamlit Web UI for interactive usage |

---

## 📂 Project Structure

```bash
Assignment/
├── app.py                   # 🎨 Streamlit Frontend
├── main.py                  # 🧠 Main Orchestrator (Backend)
├── demo.py                  # ⚡ Logic Demo (No API needed)
├── src/
│   ├── agents/              # Form-specific Agents (1040, Sch C, Sch SE)
│   ├── tools/               # Deterministic Tools (Tax Tables, Deductions)
│   └── verifiers/           # Verification System
├── data/
│   └── tax_calc_bench/      # Test Cases (JSON inputs)
└── docs/                    # Detailed Documentation
```

## 🛠️ Configuration

To switch from **Mock Mode** to **Real LLM Mode**:

1. Rename `.env.example` to `.env`.
2. Add your API Key:
   ```bash
   OPENAI_API_KEY=sk-your-key
   # OR
   ANTHROPIC_API_KEY=your-key
   ```
3. Run without the `--mock` flag.

---

**Built by Raza Ali Karimi**
