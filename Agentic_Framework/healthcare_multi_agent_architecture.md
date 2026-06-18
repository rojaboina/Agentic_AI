# Healthcare Multi-Agent Case Review Pipeline

## One-Line Project Description

Build a multi-agent healthcare case review pipeline that extracts patient data, checks clinical rules, assesses risk, flags medication/guideline issues, routes high-risk cases to human review, and generates an auditable care summary.

## Project Overview

This project adapts a multi-agent review architecture to healthcare. The goal is to support clinical case review, care-gap analysis, prior authorization review, medication safety review, or patient risk triage.

The system should act as a clinical decision-support assistant, not an autonomous diagnosis or treatment engine. It should summarize evidence, flag risks, apply deterministic rules where possible, and escalate high-risk or low-confidence cases to a human clinician.

## Building Blocks

### 1. Patient Record Input

Ingests healthcare documents and structured data such as:

- Clinical notes
- Lab reports
- Medication lists
- Diagnoses
- Allergies
- Prior visits
- Imaging summaries
- Prior authorization requests
- Discharge summaries

### 2. Clinical Extractor

Uses an LLM with structured output to convert messy clinical text into a validated schema.

Example schema:

```python
class PatientCase(BaseModel):
    patient_age: int
    sex: str
    diagnoses: list[str]
    medications: list[str]
    allergies: list[str]
    lab_results: dict[str, float]
    symptoms: list[str]
    recent_visits: list[str]
    requested_service: str | None
```

Purpose:

```text
Raw clinical text -> structured patient case
```

### 3. Guideline / Policy Check

Runs deterministic Python rules for items that should not depend on LLM judgment.

Examples:

- Required labs are present
- Patient meets age-based screening criteria
- Medication is contraindicated for a known allergy
- Required prior authorization documentation is present
- Abnormal lab thresholds are flagged
- Duplicate therapy is detected
- Coverage policy criteria are met or missing

This should be LLM-free where possible because hard rules need deterministic behavior.

### 4. Clinical Risk Analyst

Uses an LLM with structured output to interpret the patient case qualitatively.

It can assess:

- Clinical severity
- Red flags
- Care gaps
- Possible follow-up needs
- Overall risk level
- Missing information

Example output:

```python
class ClinicalRiskAnalysis(BaseModel):
    summary: str
    severity: Literal["low", "medium", "high"]
    red_flags: list[str]
    care_gaps: list[str]
    confidence: float
```

### 5. Medication Safety Agent

Checks medications against allergies, duplicate therapies, high-risk combinations, and patient-specific risk factors.

This can combine:

- Deterministic rules
- Drug interaction tools
- LLM explanation layer

Example checks:

- Drug-allergy conflict
- Duplicate medication class
- Age-specific medication concern
- High-risk medication combination
- Missing monitoring lab

### 6. Risk Quantifier

Uses tool-based scoring functions to produce numeric risk scores.

Example tools:

```python
calc_readmission_risk(patient_case) -> float
calc_medication_safety_risk(patient_case) -> float
calc_care_gap_risk(patient_case) -> float
```

Purpose:

```text
Qualitative case data -> numeric risk scores
```

### 7. Synthesizer

Combines all specialist outputs into a single clinical decision-support summary.

Inputs:

- Structured patient case
- Guideline/policy result
- Clinical risk analysis
- Medication safety result
- Quantified risk scores

Output:

```python
class ClinicalPanelDecision(BaseModel):
    decision: Literal["Routine", "Needs Follow-Up", "Urgent Review", "Insufficient Data"]
    confidence: float
    rationale: str
    recommended_actions: list[str]
    escalate_to_human: bool
```

### 8. Human Review

Routes cases to clinician review when needed.

Escalation triggers:

- High clinical risk
- Low confidence
- Possible medication safety issue
- Urgent abnormal lab
- Missing critical data
- Coverage denial recommendation
- Any safety-critical recommendation

### 9. Report Generator

Produces a structured, auditable report.

Sections:

- Patient Case Summary
- Extracted Data
- Guideline / Policy Check
- Clinical Risk Analysis
- Medication Safety Findings
- Risk Scores
- Final Recommendation
- Human Review Notes
- Audit Log

## Technical Components

Recommended stack:

```text
Python
LangGraph
Pydantic structured outputs
SQLite or Postgres for state
Pure Python rules engine
Tool functions for risk scoring
LLM agents for interpretation
Human-in-the-loop review
Checkpointing / audit logs
Markdown or PDF report output
```

## Architecture Diagram

Plain-text version:

```text
Synthetic Patient Cases
        |
        v
Pydantic PatientCase Validation
        |
        v
Extractor
normalize case, labs, vitals, medications, note signals
        |
        v
LangGraph StateGraph
shared CaseReviewState
        |
        v
+----------------------+------------------------+
|                      |                        |
v                      v                        v
Guideline Rules        Medication Safety        Risk Scoring
deterministic          deterministic            numeric risk scores
        |                      |                        |
        +----------------------+------------------------+
                               |
                               v
Specialist Agents
LLM if OPENAI_API_KEY exists, deterministic fallback otherwise
        |
        +--> Clinical Risk Agent
        +--> Medication Safety Agent
        +--> Care Management Agent
        +--> Service Review Agent
        |
        v
Human Review Router
deterministic route + optional LLM route + routing guardrails
        |
        v
Panel Decision
deterministic decision + optional LLM decision + panel guardrails
        |
        v
Final Case Decision JSON
        |
        v
Dashboard API /api/cases
        |
        v
Browser UI Dashboard
case list, decision trail, risk scores, routing, agent outputs

.env provides optional OPENAI_API_KEY for LLM nodes.
.gitignore protects .env from being committed.
```


## Core Flow

```text
1. Ingest patient record.
2. Extract structured patient data.
3. Run deterministic guideline and policy checks.
4. Run clinical risk analysis.
5. Run medication safety analysis.
6. Run tool-based risk scoring.
7. Synthesize all specialist outputs.
8. Escalate to human clinician if needed.
9. Generate auditable care summary.
```

## Design Decisions

### Parallel Specialists Instead of Sequential Chain

Clinical risk, medication safety, and guideline checks can run independently after extraction. Running them in parallel reduces wall-clock time.

### Pydantic Structured Output Instead of Regex

Clinical extraction should return validated structured data. Regex parsing is fragile and unsafe for messy clinical text.

### Deterministic Rules for Safety and Policy

Medication allergy conflicts, missing labs, and coverage criteria should use deterministic rules when possible. LLMs can explain results, but should not be the source of truth for hard rules.

### Tool-Based Risk Quantification

Risk scores should come from explicit functions or validated models, not free-form LLM guesses.

### Human-in-the-Loop for Safety

High-risk, low-confidence, or safety-critical cases should pause for clinician review.

### Auditability

Every extracted field, specialist output, decision, and human review action should be stored for traceability.

## Safety and Compliance Notes

This system should be treated as clinical decision support.

It should not:

- Diagnose autonomously
- Prescribe treatment independently
- Replace clinician judgment
- Hide uncertainty
- Store PHI insecurely

Production requirements would include:

- HIPAA-aware storage
- Access control
- Encryption
- Audit logs
- PHI minimization
- Clinical validation
- Human review workflows
