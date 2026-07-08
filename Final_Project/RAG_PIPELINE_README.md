# Patient Health RAG Pipeline

This pipeline reads local patient PDFs, extracts text, chunks lab results by panel and metric, embeds each chunk, and stores the vectors in Pinecone.

## Flow

```text
sample_patient_data/
  P001_Ava_Patel/lab_results_2022.pdf ... lab_results_2026.pdf
  P002_Michael_Johnson/lab_results_2022.pdf ... lab_results_2026.pdf
        |
        v
pypdf text extraction
        |
        v
section-aware chunking
  - primary split: lab panel
  - secondary split: metric/result block
  - fallback split: character window with overlap
        |
        v
S-PubMedBert-MS-MARCO embeddings
        |
        v
Pinecone cosine index
        |
        v
patient_id-filtered semantic retrieval
```

## Why This Chunking Strategy

The lab PDFs are organized by clinical panels and metrics:

- COMPREHENSIVE METABOLIC PANEL (CMP)
- LIPID PANEL
- VITAMIN D 25 HYDROXY
- HEMOGLOBIN A1C
- Thyroid Hormone Tests
- VITAMIN B12
- IRON AND TOTAL IRON BINDING CAPACITY (TIBC)

The chunker tries to keep a complete metric together:

```text
Glucose
View trends
Normal range: 70 - 140 mg/dL
Value
132
Interpretive Data...
```

This is better than blind fixed-size splitting because the retrieved evidence stays clinically coherent.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-rag.txt
```

## Configure

Create a `.env` or export these variables:

```bash
export PINECONE_API_KEY="your_key"
export PINECONE_INDEX_NAME="patient-health-rag"
export PINECONE_CLOUD="aws"
export PINECONE_REGION="us-east-1"
```

## Dry Run

This validates PDF extraction and chunking without embeddings or Pinecone:

```bash
python ingest_pdfs_to_pinecone.py --dry-run
```

## Ingest To Pinecone

```bash
python ingest_pdfs_to_pinecone.py
```

When regenerating the sample PDFs or changing chunking logic, refresh Pinecone cleanly:

```bash
python ingest_pdfs_to_pinecone.py --reset-namespace
```

## Retrieve Evidence

```bash
python query_pinecone.py \
  --patient-id P002 \
  --question "Why is my LDL high?"
```

The query uses:

1. the same embedding model for the question,
2. Pinecone cosine similarity search,
3. a metadata filter so only that patient's chunks are searched.
