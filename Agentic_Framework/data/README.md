# Synthetic Healthcare Dataset

This folder contains generated synthetic healthcare cases for the multi-agent case review pipeline.
The current dataset has 25 cases covering routine, urgent, medication safety, care gap, prior authorization, behavioral health, pediatric, pregnancy, oncology, post-operative, chronic disease, and social risk scenarios.

## File

```text
synthetic_patient_cases.json
```

## Important Note

These records are fully synthetic and are not real patient data. They are intended for demo, architecture, and local development use only.

## Included Fields

- `case_id`
- `synthetic`
- `patient_age`
- `sex`
- `chief_concern`
- `diagnoses`
- `medications`
- `allergies`
- `lab_results`
- `vitals`
- `recent_visits`
- `requested_service`
- `clinical_note`
- `expected_triggers`
- `expected_human_review`

## Why Generate Synthetic Data

Healthcare workflows involve PHI and safety-sensitive information. Synthetic records allow us to build and test the multi-agent architecture without exposing real patient data.

## Current Variety

- Cardiology and heart failure risk
- Diabetes, hypertension, asthma, COPD, and CKD
- Medication safety, anticoagulation, renal dosing, and controlled substances
- Pediatrics, pregnancy, oncology, post-operative, wound care, and behavioral health
- Preventive screening, prior authorization, DME renewal, and care management
- Social risk factors such as housing instability and medication access barriers

## Future Option

For a much larger synthetic dataset, use Synthea-generated patient records. Synthea is a common open-source synthetic patient generator, but this project uses a hand-generated dataset for easier demo control and predictable edge cases.
