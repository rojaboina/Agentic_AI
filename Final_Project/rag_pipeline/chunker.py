from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from rag_pipeline.pdf_loader import PdfPage


PANEL_HEADINGS = {
    "COMPREHENSIVE METABOLIC PANEL (CMP)",
    "LIPID PANEL",
    "Lipid panel:",
    "VITAMIN D 25 HYDROXY",
    "HEMOGLOBIN A1C",
    "Thyroid Hormone Tests",
    "VITAMIN B12",
    "IRON AND TOTAL IRON BINDING CAPACITY (TIBC)",
    "Additional information",
}


METRIC_NAMES = {
    "Sodium",
    "Potassium",
    "Chloride",
    "Carbon Dioxide (CO2)",
    "Urea Nitrogen (BUN)",
    "Creatinine",
    "Glucose",
    "Calcium",
    "AST (Aspartate Aminotransferase)",
    "ALT (Alanine Aminotransferase)",
    "Bilirubin, Total",
    "Alk Phos (Alkaline Phosphatase)",
    "Albumin",
    "Protein, Total",
    "Anion Gap",
    "BUN/CREA Ratio",
    "Glomerular Filtration Rate (eGFR)",
    "Cholesterol, Total",
    "LDL Calculated",
    "HDL",
    "Triglyceride",
    "Vitamin D Total, 25OH",
    "Hemoglobin A1C",
    "Average Blood Glucose (Calculated From HgBA1c Level)",
    "Thyroid Stimulating Hormone (TSH)",
    "Thyroxine, Free (FT4)",
    "Vitamin B12",
    "Iron",
    "Total Iron Binding Capacity (TIBC)",
    "Percent Transferrin Saturation",
}


@dataclass(frozen=True)
class DocumentChunk:
    id: str
    patient_id: str
    patient_name: str
    document_type: str
    year: int | None
    file_name: str
    file_path: str
    page_number: int
    chunk_index: int
    panel: str
    metric: str
    text: str

    def metadata(self) -> dict:
        metadata = {
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "document_type": self.document_type,
            "year": self.year,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "page_number": self.page_number,
            "chunk_index": self.chunk_index,
            "panel": self.panel,
            "metric": self.metric,
            "chunk_text": self.text,
        }
        return {key: value for key, value in metadata.items() if value is not None}


def chunk_pages(
    pages: list[PdfPage], max_chars: int = 2400, overlap_chars: int = 250
) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for page in pages:
        page_chunks = chunk_page(page, max_chars=max_chars, overlap_chars=overlap_chars)
        chunks.extend(page_chunks)
    return chunks


def chunk_page(page: PdfPage, max_chars: int, overlap_chars: int) -> list[DocumentChunk]:
    if page.document_type == "patient_information":
        return make_fallback_chunks(page, "Patient Information", "", page.text, max_chars, overlap_chars)

    blocks = split_lab_page_into_metric_blocks(page.text)
    chunks: list[DocumentChunk] = []
    for panel, metric, block_text in blocks:
        if len(block_text) <= max_chars:
            chunks.append(build_chunk(page, len(chunks), panel, metric, block_text))
        else:
            for sub_text in split_text_with_overlap(block_text, max_chars, overlap_chars):
                chunks.append(build_chunk(page, len(chunks), panel, metric, sub_text))
    return chunks


def split_lab_page_into_metric_blocks(text: str) -> list[tuple[str, str, str]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    current_panel = ""
    current_metric = ""
    buffer: list[str] = []
    blocks: list[tuple[str, str, str]] = []

    def flush() -> None:
        if buffer:
            blocks.append((current_panel, current_metric, "\n".join(buffer).strip()))

    for line in lines:
        if line in PANEL_HEADINGS:
            flush()
            current_panel = normalize_panel_name(line)
            current_metric = ""
            buffer = [line]
            continue

        if line in METRIC_NAMES:
            if line == current_metric:
                buffer.append(line)
                continue
            flush()
            current_metric = line
            buffer = [current_panel, line] if current_panel else [line]
            continue

        buffer.append(line)

    flush()
    return [block for block in blocks if block[2]]


def normalize_panel_name(panel: str) -> str:
    if panel == "Lipid panel:":
        return "LIPID PANEL"
    return panel


def make_fallback_chunks(
    page: PdfPage,
    panel: str,
    metric: str,
    text: str,
    max_chars: int,
    overlap_chars: int,
) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for sub_text in split_text_with_overlap(text, max_chars, overlap_chars):
        chunks.append(build_chunk(page, len(chunks), panel, metric, sub_text))
    return chunks


def split_text_with_overlap(text: str, max_chars: int, overlap_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        split_at = find_natural_split(text, start, end)
        chunks.append(text[start:split_at].strip())
        if split_at >= len(text):
            break
        start = max(0, split_at - overlap_chars)
    return [chunk for chunk in chunks if chunk]


def find_natural_split(text: str, start: int, end: int) -> int:
    window = text[start:end]
    matches = list(re.finditer(r"\n\n|\n[A-Z][^\n]{0,80}\n", window))
    if matches:
        candidate = start + matches[-1].start()
        if candidate > start + 400:
            return candidate
    return end


def build_chunk(
    page: PdfPage, chunk_index: int, panel: str, metric: str, text: str
) -> DocumentChunk:
    source = f"{page.patient_id}|{page.file_name}|{page.page_number}|{chunk_index}|{text[:100]}"
    chunk_id = hashlib.sha1(source.encode("utf-8")).hexdigest()
    return DocumentChunk(
        id=chunk_id,
        patient_id=page.patient_id,
        patient_name=page.patient_name,
        document_type=page.document_type,
        year=page.year,
        file_name=page.file_name,
        file_path=page.file_path,
        page_number=page.page_number,
        chunk_index=chunk_index,
        panel=panel,
        metric=metric,
        text=text,
    )
