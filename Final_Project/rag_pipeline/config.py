from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_DATA_DIR = Path(
    "/Users/roja/Documents/Agentic_AI/Final_Project/sample_patient_data"
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_env_file(path: Path | None = None) -> None:
    env_path = path or PROJECT_ROOT / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    data_dir: Path = DEFAULT_DATA_DIR
    embedding_model_name: str = "pritamdeka/S-PubMedBert-MS-MARCO"
    embedding_dimension: int = 768
    pinecone_index_name: str = "patient-health-rag"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    chunk_max_chars: int = 2400
    chunk_overlap_chars: int = 250

    @classmethod
    def from_env(cls) -> "Settings":
        load_env_file()
        return cls(
            data_dir=Path(os.getenv("PATIENT_DATA_DIR", str(DEFAULT_DATA_DIR))).expanduser(),
            embedding_model_name=os.getenv(
                "EMBEDDING_MODEL_NAME", "pritamdeka/S-PubMedBert-MS-MARCO"
            ),
            embedding_dimension=int(os.getenv("EMBEDDING_DIMENSION", "768")),
            pinecone_index_name=os.getenv("PINECONE_INDEX_NAME", "patient-health-rag"),
            pinecone_cloud=os.getenv("PINECONE_CLOUD", "aws"),
            pinecone_region=os.getenv("PINECONE_REGION", "us-east-1"),
            chunk_max_chars=int(os.getenv("CHUNK_MAX_CHARS", "2400")),
            chunk_overlap_chars=int(os.getenv("CHUNK_OVERLAP_CHARS", "250")),
        )


def require_env(name: str) -> str:
    load_env_file()
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
