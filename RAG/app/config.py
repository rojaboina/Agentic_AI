from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DB_DIR = PROJECT_ROOT / "db"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


@dataclass(frozen=True)
class Settings:
    project_root: Path
    data_dir: Path
    db_dir: Path
    outputs_dir: Path
    sqlite_path: Path
    pinecone_api_key: str | None
    pinecone_index_name: str
    pinecone_cloud: str
    pinecone_region: str
    pinecone_embed_model: str
    pinecone_embed_text_field: str


def load_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env")

    sqlite_path = Path(os.getenv("SQLITE_PATH", DB_DIR / "book_rag.sqlite3"))
    if not sqlite_path.is_absolute():
        sqlite_path = PROJECT_ROOT / sqlite_path

    return Settings(
        project_root=PROJECT_ROOT,
        data_dir=DATA_DIR,
        db_dir=DB_DIR,
        outputs_dir=OUTPUTS_DIR,
        sqlite_path=sqlite_path,
        pinecone_api_key=os.getenv("PINECONE_API_KEY") or None,
        pinecone_index_name=os.getenv("PINECONE_INDEX_NAME", "book-rag"),
        pinecone_cloud=os.getenv("PINECONE_CLOUD", "aws"),
        pinecone_region=os.getenv("PINECONE_REGION", "us-east-1"),
        pinecone_embed_model=os.getenv("PINECONE_EMBED_MODEL", "llama-text-embed-v2"),
        pinecone_embed_text_field=os.getenv("PINECONE_EMBED_TEXT_FIELD", "chunk_text"),
    )
