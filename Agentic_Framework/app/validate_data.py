from __future__ import annotations

import json
from pathlib import Path

from app.schemas import PatientCase


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "synthetic_patient_cases.json"


def load_patient_cases() -> list[PatientCase]:
    raw_cases = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return [PatientCase.model_validate(case) for case in raw_cases]


def main() -> None:
    cases = load_patient_cases()
    print(f"validated_cases={len(cases)}")
    print(f"first_case={cases[0].case_id}")


if __name__ == "__main__":
    main()
