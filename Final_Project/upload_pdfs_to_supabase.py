from __future__ import annotations

import argparse
import json
import mimetypes
import os
import urllib.error
import urllib.request
from pathlib import Path

from rag_pipeline.config import Settings, load_env_file


DEFAULT_BUCKET = "patient-pdfs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload patient PDFs to Supabase Storage.")
    parser.add_argument("--bucket", default=os.getenv("SUPABASE_STORAGE_BUCKET", DEFAULT_BUCKET))
    parser.add_argument(
        "--create-bucket",
        action="store_true",
        help="Create the Supabase Storage bucket if it does not already exist.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be uploaded without calling Supabase.",
    )
    parser.add_argument(
        "--manifest",
        default="supabase_pdf_manifest.json",
        help="Path for the upload manifest JSON.",
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


def iter_pdfs(data_dir: Path) -> list[Path]:
    return sorted(path for path in data_dir.glob("P*/*.pdf") if path.is_file())


def storage_object_path(data_dir: Path, pdf_path: Path) -> str:
    return pdf_path.relative_to(data_dir).as_posix()


def request_json(url: str, key: str, method: str, payload: dict | None = None) -> dict:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def create_bucket_if_needed(base_url: str, key: str, bucket: str) -> None:
    try:
        request_json(f"{base_url}/storage/v1/bucket/{bucket}", key, "GET")
        print(f"Bucket already exists: {bucket}")
        return
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        is_missing_bucket = exc.code == 404 or "Bucket not found" in body
        if not is_missing_bucket:
            raise

    request_json(
        f"{base_url}/storage/v1/bucket",
        key,
        "POST",
        {"id": bucket, "name": bucket, "public": False},
    )
    print(f"Created private bucket: {bucket}")


def upload_pdf(base_url: str, key: str, bucket: str, object_path: str, pdf_path: Path) -> dict:
    content_type = mimetypes.guess_type(pdf_path.name)[0] or "application/pdf"
    request = urllib.request.Request(
        f"{base_url}/storage/v1/object/{bucket}/{object_path}",
        data=pdf_path.read_bytes(),
        method="POST",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": content_type,
            "x-upsert": "true",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def main() -> None:
    args = parse_args()
    settings = Settings.from_env()
    pdfs = iter_pdfs(settings.data_dir)

    print(f"PDF source: {settings.data_dir}")
    print(f"PDF count: {len(pdfs)}")
    print(f"Supabase bucket: {args.bucket}")

    if args.dry_run:
        for pdf_path in pdfs:
            print(f"DRY RUN {pdf_path} -> {args.bucket}/{storage_object_path(settings.data_dir, pdf_path)}")
        print("Dry run complete. No files were uploaded.")
        return

    base_url, key = require_supabase_config()
    if args.create_bucket:
        create_bucket_if_needed(base_url, key, args.bucket)

    manifest = []
    for pdf_path in pdfs:
        object_path = storage_object_path(settings.data_dir, pdf_path)
        upload_pdf(base_url, key, args.bucket, object_path, pdf_path)
        entry = {
            "local_path": str(pdf_path),
            "bucket": args.bucket,
            "object_path": object_path,
            "storage_url": f"{base_url}/storage/v1/object/{args.bucket}/{object_path}",
        }
        manifest.append(entry)
        print(f"Uploaded {object_path}")

    manifest_path = Path(args.manifest)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nUploaded {len(manifest)} PDFs.")
    print(f"Manifest written to {manifest_path}")


if __name__ == "__main__":
    main()
