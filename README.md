# Vaulty — AI Exception Intelligence

<p align="center">
  <strong>Investigate. Resolve. Remember.</strong>
</p>

<p align="center">
  An agentic Accounts Payable exception intelligence system that investigates invoice discrepancies using current business evidence and relevant experience from previous cases.
</p>

---

## 🚀 Overview

Accounts Payable systems are good at detecting invoice mismatches.

The harder problem is understanding **why** the mismatch happened and deciding what should happen next.

A price difference, for example, could be caused by:

- An approved contract amendment
- An incorrect vendor charge
- Partial delivery
- A missing purchase order
- A duplicate invoice
- Tax, currency, or rounding differences
- Freight or additional charges
- An expired contract

Vaulty turns exception handling into an **agentic investigation workflow**.

It brings together invoice, purchase order, receipt, contract, vendor context, and previous case experience to investigate an exception and produce an explainable resolution.

The key idea is:

> **Memory guides the investigation. Current evidence decides the outcome.**

---

## 🎯 The Problem

Traditional invoice matching can tell an AP team:

```text
Invoice Price ≠ Purchase Order Price

But it cannot necessarily explain:

Why is the price different?

Was there an approved amendment?

Has this happened before?

How was the previous case resolved?

Does that previous experience apply to this case?

What should happen now?

Vaulty focuses on this investigation layer.

Instead of treating every exception as a completely new problem, it allows previous resolved cases to become useful organizational experience.

🧠 How Vaulty Works

Vaulty follows a memory-aware investigation loop:

              NEW EXCEPTION
                    │
                    ▼
                 TRIAGE
                    │
                    ▼
              INVESTIGATION
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
   CURRENT EVIDENCE      PAST EXPERIENCE
          │                   │
          └─────────┬─────────┘
                    ▼
                  VERIFY
                    │
             ┌──────┴──────┐
             │             │
             ▼             ▼
         CONFIRMED    CONTRADICTED
             │             │
             └──────┬──────┘
                    ▼
                RESOLUTION
                    │
                    ▼
             HUMAN DECISION
                    │
                    ▼
                REFLECTION
                    │
                    ▼
              NEW EXPERIENCE

The important part is that memory is not treated as truth.

Previous experience is recalled and evaluated against the evidence in the current case.

🔄 Hindsight Memory

Vaulty uses Hindsight as its agent memory layer.

The memory lifecycle is:

RETAIN
   ↓
RECALL
   ↓
VERIFY
   ↓
RESOLVE
   ↓
REFLECT
   ↓
RETAIN
Retain

After an investigation is completed, Vaulty retains relevant experience from the case.

This can include:

Investigation context
Business evidence
Exception type
Resolution
Human decision
Important observations
Recall

When a similar exception appears later, Vaulty retrieves relevant previous experience.

Verify

The recalled experience is compared against the current evidence.

The system classifies the relationship as:

CONFIRMED
CONTRADICTED
INSUFFICIENT
Reflect

The final outcome and human decision become part of future organizational experience.

🧾 Example: Same Vendor, Different Outcome

Consider an ACME invoice.

Previous case
Invoice Price:        $120
PO Price:             $100
Approved Amendment:   $120

Vaulty investigates the discrepancy and finds an approved amendment.

The case is resolved and the experience is retained.

New case

A similar ACME invoice arrives:

Invoice Price:        $120
PO Price:             $100
Approved Amendment:   None

Vaulty recalls the previous ACME experience.

But it does not automatically repeat the previous decision.

It checks the current evidence.

Past Experience
"ACME price variance was previously legitimate."

                +

Current Evidence
"No matching approved amendment."

                ↓

       CONTRADICTED

The system can therefore adapt its recommendation:

Payment: HOLD

Action:
Draft vendor query regarding the unamended rate.

Reason:
Current evidence does not support the previous exception.

This demonstrates the central behavior of Vaulty:

Remember what happened before.
Check what is happening now.
Then decide.

🤖 Multi-Agent Architecture

Vaulty uses specialized agents for different stages of the workflow.

Triage Agent

Identifies and categorizes the exception.

Examples:

Price mismatch
Quantity mismatch
Missing PO
Duplicate invoice
Partial delivery
Tax discrepancy
Contract issue
Investigation Agent

Investigates the exception using current business evidence and relevant previous experience.

It determines whether historical experience is:

Confirmed
Contradicted
Insufficient
Resolution Agent

Produces an actionable resolution based on the investigation.

Possible outcomes include:

Approve
Hold payment
Draft vendor query
Request additional evidence
Escalate for human review
Orchestrator

Coordinates the complete agent workflow.

Reflection Agent

Captures the completed case and human outcome as reusable organizational experience.

🏗️ Architecture
                   ┌─────────────────┐
                   │   Streamlit UI  │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  Orchestrator   │
                   └────────┬────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
          ┌───────────┐         ┌──────────────┐
          │   Triage  │         │    Business  │
          │   Agent   │         │    Evidence  │
          └─────┬─────┘         └──────┬───────┘
                │                      │
                └──────────┬───────────┘
                           ▼
                  ┌────────────────┐
                  │  Investigation │
                  │      Agent     │
                  └───────┬────────┘
                          │
                 ┌────────┴────────┐
                 │                 │
                 ▼                 ▼
          Current Evidence   Hindsight Memory
                 │                 │
                 └────────┬────────┘
                          ▼
                  ┌────────────────┐
                  │   Resolution   │
                  │      Agent     │
                  └───────┬────────┘
                          │
                          ▼
                   Human Decision
                          │
                          ▼
                    Reflection
                          │
                          ▼
                  Hindsight Memory
👁️ Explainable Memory Influence

Vaulty makes memory influence visible in the interface.

The VAULTY REMEMBERED section shows:

Past Experience

What happened in a relevant previous case.

Current Evidence

What the system found in the current case.

Verdict
CONFIRMED
CONTRADICTED
INSUFFICIENT
Adapted Decision

The resulting recommendation after comparing historical experience with current evidence.

For example:

Past experience suggested this variance could be legitimate, but the current case contains no matching approved amendment.

Evidence overrides memory.

This makes the role of memory explicit rather than hiding it inside the model's response.

👤 Human-in-the-Loop

Vaulty is designed to assist AP teams rather than silently make financial decisions.

The system can:

Investigate exceptions
Gather relevant evidence
Recall previous experience
Explain conflicts
Recommend a resolution
Draft vendor queries
Escalate uncertain cases

Final payment decisions remain human-gated.

AI Investigation
       ↓
Evidence + Recommendation
       ↓
Human Review
       ↓
Final Decision
📋 Supported Exception Scenarios

Vaulty's investigation workflow is designed to handle scenarios such as:

Exception	Investigation Focus
Price mismatch	Contract and amendment history
Quantity mismatch	PO and receipt
Partial delivery	Receipt and fulfillment
Missing PO	Purchasing and vendor context
Duplicate invoice	Invoice history
Invoice before receipt	Transaction timeline
Tax discrepancy	Tax evidence
Currency / rounding	Transaction details
Freight	Contract and invoice charges
Split billing	Related transactions
Credit note / rebate	Vendor history
Missed discount	Contract terms
Expired contract	Contract validity
🛠️ Tech Stack
Technology	Purpose
Python	Core application and agent logic
Streamlit	Web application and UI
Groq / LLM	Agent reasoning
Hindsight	Agent memory
Function Calling	Tool-based agent interaction
JSON	Prototype business data
Git / GitHub	Version control
📁 Project Structure
Vaulty/
│
├── agents/
│   ├── pipeline.py
│   ├── triage.py
│   ├── investigator.py
│   ├── resolution.py
│   ├── orchestrator.py
│   └── reflection.py
│
├── memory/
│   ├── hindsight_client.py
│   ├── fallback_memory.py
│   └── memory_repository.py
│
├── repositories/
│   └── business_repository.py
│
├── services/
│   └── analytics_service.py
│
├── ui/
│   ├── pages.py
│   ├── components.py
│   └── styles.py
│
├── data/
│   └── ...
│
├── tests/
│   └── test_vaulty.py
│
├── scripts/
│   └── ...
│
├── app.py
├── requirements.txt
└── README.md
⚙️ Getting Started
Prerequisites
Python 3.10+
pip
Git
Groq API key
Hindsight configuration
1. Clone the repository
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd Vaulty
2. Create a virtual environment
Windows
python -m venv .venv
.venv\Scripts\activate
macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
3. Install dependencies
pip install -r requirements.txt
4. Configure environment variables

Create a .env file:

GROQ_API_KEY=your_groq_api_key

HINDSIGHT_API_URL=your_hindsight_api_url
HINDSIGHT_API_KEY=your_hindsight_api_key
HINDSIGHT_BANK_ID=vaulty-ap-memory

Never commit API keys or secrets to GitHub.

5. Run the application
streamlit run app.py

Vaulty will be available at the local Streamlit URL displayed in the terminal.

🧪 Testing

Run the test suite:

pytest tests/test_vaulty.py

The tests cover core behavior including:

Memory recall
Evidence verification
Confirmed memory
Contradicted memory
Evidence overriding memory
Adapted resolution behavior

You can also verify the project compiles successfully:

python -m compileall .
💾 Current Data Layer

The current prototype uses its existing local/static business data layer to demonstrate the AP investigation workflow.

The prototype focuses on the agentic investigation and memory architecture rather than enterprise database infrastructure.

The current implementation does not depend on Supabase.

A persistent enterprise database can be introduced later without changing the core agent and memory workflow.

🔐 Security

The current version is a prototype.

For production deployment, additional controls would be required, including:

Authentication
Role-based authorization
Secure secret management
Audit logging
Encryption
Data access controls
Enterprise data retention policies

API keys should always be stored through environment variables or a secure secret manager.

🚧 Current Limitations

Vaulty currently focuses on demonstrating the agentic exception investigation workflow.

The prototype does not yet include:

Enterprise ERP integrations
Production authentication
Enterprise role management
Automated payment release
Production-grade audit infrastructure
Automated vendor communication

These are potential extensions for a production deployment.

🔮 Future Scope

A production version of Vaulty could integrate with ERP and AP platforms:

ERP / AP System
       │
       ▼
Invoices / POs / Receipts
       │
       ▼
Exception Detection
       │
       ▼
Vaulty Investigation
       │
       ├── Current Evidence
       │
       └── Hindsight Memory
       │
       ▼
Resolution
       │
       ▼
Human Approval
       │
       ▼
ERP / AP Workflow

Potential future capabilities include:

ERP/AP integrations
Persistent case management
Role-based access control
Audit trails
Vendor communication workflows
Advanced analytics
Risk-based escalation
Enterprise observability
Governance and compliance controls
💡 Why Agent Memory Matters

Without memory:

Case
 ↓
Investigate
 ↓
Resolve
 ↓
Forget

With Vaulty:

Case
 ↓
Investigate
 ↓
Resolve
 ↓
Remember
 ↓
Future Case
 ↓
Recall
 ↓
Verify
 ↓
Adapt

The goal is not simply to make an AI remember more.

The goal is to make previous experience useful at the right time while still allowing current evidence to change the conclusion.

🎯 The Core Takeaway

Vaulty turns Accounts Payable exception handling from:

Detect → Escalate

into:

Detect
   ↓
Investigate
   ↓
Recall
   ↓
Verify
   ↓
Resolve
   ↓
Learn

It remembers previous investigations.

It recalls relevant experience.

It checks that experience against the current case.

It adapts when the evidence disagrees.

And the final business decision remains human-gated.

Vaulty
Investigate. Resolve. Remember.

Memory guides the investigation.
Current evidence decides the outcome.

🔗 Resources
Hindsight
GitHub: https://github.com/vectorize-io/hindsight
Documentation: https://hindsight.vectorize.io/
<p align="center"> Built with Python · Streamlit · Groq · Hindsight · Agentic AI </p> ```
What I'd put at the very top of the actual GitHub repo

Don't leave it as just text. Add a screenshot right below the intro:

Vaulty
Investigate. Resolve. Remember.


Memory guides the investigation.
Current evidence decides the outcome.
