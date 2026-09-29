# Vaulty — AI Exception Intelligence

### Investigate. Resolve. Remember.

Vaulty is an AI-powered Accounts Payable (AP) exception intelligence system that investigates invoice discrepancies using business evidence, previous case experience, and multi-agent reasoning.

Instead of simply flagging that an invoice does not match a purchase order, Vaulty investigates **why** the exception happened, determines what evidence supports the case, recalls relevant previous resolutions, and produces an explainable resolution recommendation.

> **Memory guides the investigation. Current evidence decides the outcome.**

---

## Why Vaulty?

Traditional invoice automation is good at identifying mismatches.

The difficult part begins after the mismatch is detected.

A price difference could be caused by:

- An approved contract amendment
- Incorrect vendor pricing
- Partial delivery
- Missing purchase order
- Duplicate billing
- Tax or currency differences
- Freight or additional charges
- Split or consolidated billing
- Credit notes or rebates
- Missed discounts
- An expired contract
- A potentially suspicious transaction

The same type of exception may also have been investigated and resolved differently in the past.

Vaulty combines **current business evidence** with **organizational memory** so that previous experience can inform a new investigation without blindly determining its outcome.

---

# Core Concept

Vaulty follows a simple learning loop:

```text
        CURRENT CASE
             │
             ▼
       ┌───────────┐
       │   TRIAGE  │
       └─────┬─────┘
             │
             ▼
     ┌─────────────────┐
     │  INVESTIGATION  │◄──────────────┐
     └────────┬────────┘               │
              │                        │
       ┌──────┴───────┐                │
       │              │                │
       ▼              ▼                │
 CURRENT          HINDSIGHT            │
 EVIDENCE         MEMORY               │
       │              │                │
       └──────┬───────┘                │
              │                        │
              ▼                        │
       VERIFY EXPERIENCE              │
              │                        │
       ┌──────┴──────┐                 │
       │             │                 │
       ▼             ▼                 │
   CONFIRMED     CONTRADICTED          │
       │             │                 │
       └──────┬──────┘                 │
              ▼                        │
       ┌──────────────┐               │
       │  RESOLUTION  │               │
       └──────┬───────┘               │
              │                        │
              ▼                        │
       HUMAN DECISION                 │
              │                        │
              ▼                        │
        ┌───────────┐                 │
        │ REFLECTION│─────────────────┘
        └───────────┘
              │
              ▼
       NEW EXPERIENCE
       IN MEMORY