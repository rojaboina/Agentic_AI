from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path

from rag_pipeline.config import Settings, load_env_file


DEFAULT_BUCKET = "patient-pdfs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download patient PDFs from Supabase Storage.")
    parser.add_argument("--bucket", default=os.getenv("SUPABASE_STORAGE_BUCKET", DEFAULT_BUCKET))
    parser.add_argument(
        "--manifest",
        default="supabase_pdf_manifest.json",
        help="Manifest produced by upload_pdfs_to_supabase.py.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be downloaded without writing files.",
    )
    return parser.parse_args()


def require_supabase_config() -> tuple[str, str]:
    load_env_file()
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY", "")
    if not url:
        raise RuntimeError("Missing SUPABASE_URL in .env")
    if not key:
        raise RuntimeError("Missing SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY in .env")
    return url, key


def load_manifest(path: Path) -> list[dict]:
    if not path.exists():
        raise RuntimeError(f"Missing manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def download_object(base_url: str, key: str, bucket: str, object_path: str) -> bytes:
    request = urllib.request.Request(
        f"{base_url}/storage/v1/object/{bucket}/{object_path}",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def main() -> None:
    args = parse_args()
    settings = Settings.from_env()
    manifest = load_manifest(Path(args.manifest))

    print(f"PDF destination: {settings.data_dir}")
    print(f"Manifest entries: {len(manifest)}")
    print(f"Supabase bucket: {args.bucket}")

    if args.dry_run:
        for item in manifest:
            print(f"DRY RUN {args.bucket}/{item['object_path']} -> {settings.data_dir / item['object_path']}")
        print("Dry run complete. No files were downloaded.")
        return

    base_url, key = require_supabase_config()
    for item in manifest:
        object_path = item["object_path"]
        destination = settings.data_dir / object_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(download_object(base_url, key, args.bucket, object_path))
        print(f"Downloaded {object_path}")

    print(f"\nDownloaded {len(manifest)} PDFs from Supabase Storage.")


if __name__ == "__main__":
    main()
