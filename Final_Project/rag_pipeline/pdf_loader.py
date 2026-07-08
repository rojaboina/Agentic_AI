from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from pypdf import PdfReader


@dataclass(frozen=True)
class PdfPage:
    patient_id: str
    patient_name: str
    document_type: str
    year: int | None
    file_name: str
    file_path: str
    page_number: int
    text: str


def parse_patient_folder(folder: Path) -> tuple[str, str]:
    parts = folder.name.split("_", 1)
    patient_id = parts[0]
    patient_name = parts[1].replace("_", " ") if len(parts) > 1 else folder.name
    return patient_id, patient_name


def document_type_for(pdf_path: Path) -> str:
    if "lab" in pdf_path.stem.lower():
        return "lab_results"
    if "patient" in pdf_path.stem.lower():
        return "patient_information"
    return pdf_path.stem


def year_for(pdf_path: Path) -> int | None:
    match = re.search(r"(20\d{2})", pdf_path.stem)
    return int(match.group(1)) if match else None


def iter_patient_pdfs(data_dir: Path) -> list[Path]:
    return sorted(path for path in data_dir.glob("P*/*.pdf") if path.is_file())


def extract_pdf_pages(pdf_path: Path) -> list[PdfPage]:
    patient_id, patient_name = parse_patient_folder(pdf_path.parent)
    document_type = document_type_for(pdf_path)
    year = year_for(pdf_path)
    reader = PdfReader(str(pdf_path))
    pages: list[PdfPage] = []
    for idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(
            PdfPage(
                patient_id=patient_id,
                patient_name=patient_name,
                document_type=document_type,
                year=year,
                file_name=pdf_path.name,
                file_path=str(pdf_path),
                page_number=idx,
                text=normalize_text(text),
            )
        )
    return pages


def normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.replace("\xa0", " ").splitlines()]
    cleaned: list[str] = []
    previous_blank = False
    for line in lines:
        is_blank = not line
        if is_blank and previous_blank:
            continue
        cleaned.append(line)
        previous_blank = is_blank
    return "\n".join(cleaned).strip()


def load_all_pdf_pages(data_dir: Path) -> list[PdfPage]:
    pages: list[PdfPage] = []
    for pdf_path in iter_patient_pdfs(data_dir):
        pages.extend(extract_pdf_pages(pdf_path))
    return pages
