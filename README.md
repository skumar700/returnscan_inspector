# Project 18 — ReturnScan Inspector

## What This Is
An AI-powered returns inspection system for 3rd Party Reverse Logistics 
operations. Built as a proof of concept demonstrating how a two-agent 
vision pipeline can automate product grading at warehouse scale.

## The Problem It Solves
Manual returns inspection is slow, inconsistent, and undocumented. 
A human inspector makes a judgment call on every item with no audit 
trail and no standardized reasoning. This system replaces that 
clipboard-and-intuition workflow with a structured, logged, 
auditable AI pipeline.

## Agent Architecture

### Agent 1 — Observer (Vision Agent)
- Receives a photo of the returned item
- Outputs structured factual observations in JSON
- No grading, no judgment — facts only
- Identifies: product type, brand, condition indicators, 
  packaging state, visible components

### Agent 2 — Grader (Adversarial Review Agent)
- Receives Observer's structured output — never sees raw image
- Applies adversarial challenges before reaching a verdict
- Asks: What is ambiguous? What is the worst interpretation? 
  What would a client dispute?
- Outputs: Grade (A/B/C/Scrap), disposition channel, 
  confidence level, reasoning, human review flags

## Grading Standards
| Grade | Condition | Disposition |
|-------|-----------|-------------|
| A | Original or near-original condition | Restock as new |
| B | Visible wear, minor damage, likely functional | Refurbishment / Secondary market |
| C | Significant damage, missing components | Liquidation / Parts recovery |
| Scrap | Non-functional, no recoverable value | Recycling / Disposal |

## Agentic Design Patterns Used
- **Multi-Modal Tool Use**: Vision as an input modality, not just text
- **Separation of Concerns**: Observe first, decide second
- **Adversarial Review**: Grader stress-tests before deciding
- **Human-in-the-Loop Escalation**: Flags route to human supervisor
- **Chain of Thought Transparency**: Full reasoning logged and displayed

## Audit Trail
Every inspection logs to Supabase with:
- Observer's raw response (what the AI saw)
- Observer's structured JSON output (queryable)
- Grader's adversarial challenges (reasoning chain)
- Final grade and disposition
- Human review flags
- Timestamp

This enables dispute resolution — any grade can be explained 
and defended with documented reasoning.

## Tech Stack
- **UI**: Streamlit
- **Vision Model**: Google Gemini 2.5 Flash via OpenRouter
- **Database**: Supabase (PostgreSQL + JSONB)
- **Language**: Python

## Project Structure
```
returnscan_inspector/
├── app.py              # Streamlit UI + pipeline orchestration
├── agents/
│   ├── observer.py     # Agent 1 — Vision + structured observation
│   └── grader.py       # Agent 2 — Adversarial grading
├── utils/
│   └── database.py     # Supabase logging + retrieval
├── .env                # API keys (never committed)
└── requirements.txt
```

## Business Context
Built as a POC for a 3rd Party Reverse Logistics operation handling 
consumer electronics, apparel, and general retail returns. 

The system demonstrates that AI inspection can:
1. Match human observation accuracy at machine speed
2. Apply consistent grading standards across all items
3. Produce a defensible audit trail for client disputes
4. Know what it doesn't know — flagging items for human review

## Limitations (By Design)
- Functionality cannot be assessed from photos alone — 
  physical verification required for borderline items
- Grading standards are prompt-configured, not fine-tuned — 
  Project 19 (ReturnIQ) addresses domain adaptation
- Single photo input — multi-angle capture would improve accuracy

## Connection to Project 19
Every inspection logged here feeds the ReturnIQ Decision Engine. 
The JSONB observer outputs become the knowledge base that makes 
Project 19's domain-specific grading possible.