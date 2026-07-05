# Personal Book RAG Recommender

## Project Overview

This project is a personalized RAG-based book recommendation system. It recommends one book per reading module each week based on a user's reading history, taste profile, candidate book pool, retrieval results, reranking logic, and feedback.

The current modules are:

- Autobiography / Memoir
- Self-Help / Personal Growth
- Technical
- Poetry / Reflective Writing
- Philosophy
- Spirituality

The system uses SQLite as the local source of truth and Pinecone as the semantic retrieval index. SQLite stores durable application state, including books, chunks, recommendation modules, generated intents, retrieval logs, reranking results, final recommendations, feedback, usage logs, and evaluation metrics. Pinecone stores the searchable semantic vectors using integrated embeddings.

The app also includes a local browser UI that shows weekly recommendations, source links, module filters, feedback buttons, feedback history, and semantic chat over the book memory.

## Architecture

The weekly pipeline runs in this order:

```text
pipeline.py
  -> ingest.py
  -> vector_index.py
  -> intents.py
  -> retrieve.py
  -> rerank.py
  -> recommend.py
  -> web.py / UI
```

In simple terms:

```text
Data -> Chunks -> Pinecone Vectors -> Intents -> Retrieval -> Reranking -> Recommendations -> UI
```

### Architecture Diagram

```text
                         +----------------------+
                         |     pipeline.py      |
                         |  Main Orchestrator   |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |      ingest.py       |
                         | Load Local Datasets  |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |       SQLite         |
                         |     books table      |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |      ingest.py       |
                         | build_book_chunks()  |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |       SQLite         |
                         |   book_chunks table  |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |   vector_index.py    |
                         | upsert_book_chunks() |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |       Pinecone       |
                         | Integrated Embedding |
                         |   + Vector Search    |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |      retrieve.py     |
                         | Filtered Retrieval   |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |       rerank.py      |
                         |  Custom Reranking    |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |     recommend.py     |
                         | Final Weekly Picks   |
                         +----------+-----------+
                                    |
                    +---------------+----------------+
                    |                                |
                    v                                v
          +----------------------+          +----------------------+
          |       SQLite         |          |       Markdown       |
          | recommendations table|          | weekly_recommend...  |
          +----------+-----------+          +----------------------+
                     |
                     v
          +----------------------+
          |       web.py / UI    |
          | Cards + Feedback +   |
          | Semantic Chat        |
          +----------------------+
```

### Execution Flow

```text
1. pipeline.py
   |
   | calls run_ingestion()
   v
2. ingest.py
   |
   | loads reading_history.csv
   | loads book_candidates.csv
   | loads recommendation_modules.csv
   | creates book_chunks
   v
3. vector_index.py
   |
   | creates/connects Pinecone index
   | sends chunk_text records to Pinecone
   | Pinecone creates integrated embeddings
   v
4. intents.py
   |
   | creates one recommendation intent per module
   | stores intents in SQLite
   v
5. retrieve.py
   |
   | searches Pinecone with generated intents
   | filters by status=candidate and module=current module
   | stores retrieval_runs and retrieval_results
   v
6. rerank.py
   |
   | applies custom ranking rules
   | uses module fit, feedback, source links, rating status
   | stores rerank_results
   v
7. recommend.py
   |
   | selects one book per module
   | saves recommendations in SQLite
   | writes weekly_recommendations.md
   | logs evaluation metrics
   v
8. web.py / UI
   |
   | displays recommendations
   | captures Yes / Maybe / No feedback
   | supports module filtering and semantic chat
```

Main technical decisions:

- SQLite is the source of truth because it is local, inspectable, and good for structured records.
- Pinecone is the vector database because it supports managed semantic search and integrated embeddings.
- Pinecone integrated embeddings are used instead of OpenAI embeddings to avoid a separate embedding API dependency.
- Document-level chunks are used because each book profile is naturally a compact searchable unit.
- Filtered dense retrieval is used because recommendation taste is semantic, but module boundaries still matter.
- Rule-based reranking is used because it is transparent and easy to explain in a demo.
- Final output is grounded and structured, not freely invented by an LLM.

## Datasets Used

The project currently uses local seed datasets.

### Reading History

File:

```text
data/reading_history.csv
```

This contains books already read by the user. It provides personal taste signals and prevents the system from recommending books already read.

Examples include:

- Man's Search for Meaning
- When Breath Becomes Air
- Deep Work
- Designing Data-Intensive Applications
- The Four Agreements
- You Can Heal Your Life
- The Alchemist
- Bird by Bird

### Recommendation Modules

File:

```text
data/recommendation_modules.csv
```

This defines the active recommendation categories:

- autobiography_memoir
- self_help_personal_growth
- technical
- poetry_reflective_writing
- philosophy
- spirituality

### Candidate Books

File:

```text
data/book_candidates.csv
```

This is the candidate pool of books the system can recommend. It was manually curated as a starter dataset based on the user's interests.

Examples include:

- The Choice
- The Practicing Stoic
- Devotions
- Essentialism
- The Power of Now
- AI Engineering

Each candidate includes:

```text
module
title
author
summary
themes
goodreads_rating
goodreads_rating_checked_at
source_url
notes
```

Goodreads rating fields are present, but ratings are currently marked pending unless verified. This avoids storing guessed or stale rating values.

## Prompts Used During Vibe Coding

These are representative prompts used while building the project:

```text
Can we both build a RAG together?
```

```text
I am a huge book lover. The categories I like are autobiographies, self-help, technical books, and poetry. Each week I need to get a book recommendation for each genre.
```

```text
Can you design the architecture for me?
```

```text
May be we could add philosophy and spirituality more modules.
```

```text
Every book added to my recommendation should include summary, author, date added, and Goodreads rating.
```

```text
In terms of RAG architecture we have offline architecture for ingest, chunk, embed and online part retrieve, rerank and give output. Is this right?
```

```text
Can you implement generated recommendation intents?
```

```text
Can you create a beautiful visual UI that has all these book recommendations each week with chat option and ability to say yes or no?
```

```text
Can you explain the technical decision choices and why?
```

These prompts shaped both the implementation and the architecture documentation.

## Iterations Tried

### 1. Initial Local RAG Plan

The first design used:

```text
Python
CSV first
ChromaDB later
OpenAI embeddings
Typer CLI
Markdown output
```

This was later changed as the requirements became more final and production-like.

### 2. SQLite Instead of CSV as Source of Truth

CSV was useful for seed data, but the system needed feedback, retrieval runs, reranking logs, recommendations, and evaluation metrics. SQLite became the source of truth because it supports structured records and local persistence.

### 3. Pinecone Instead of ChromaDB

The user already had a Pinecone account, so Pinecone replaced ChromaDB as the vector store.

### 4. OpenAI Embeddings Attempt

The first embedding implementation used OpenAI embeddings. This hit an `insufficient_quota` error, so the design changed.

### 5. Pinecone Integrated Embeddings

The system switched to Pinecone integrated embeddings using:

```text
llama-text-embed-v2
```

This simplified the architecture because the app sends text records to Pinecone and Pinecone handles vector creation internally.

### 6. Retrieval Was Too Broad

At first, retrieval searched all candidate books for every module. This caused cross-module matches, such as self-help books appearing in unrelated modules.

The fix was metadata-filtered dense retrieval:

```text
status = candidate
module = current module
```

### 7. UI Started as Taste-Signal Cards

Before candidate books existed, the UI could only show matches from already-read books. After candidate ingestion was added, the UI changed to real weekly recommendations.

### 8. Refinement Pass

The final refinements added:

- Human-readable explanations
- Module filter
- Source links
- Feedback history
- Semantic chat
- One-command weekly pipeline

## Learnings and Observations

### RAG Is Useful Beyond Q&A

This project shows that RAG is not only for "chat with documents." It can also power recommendation systems where retrieval finds semantically relevant candidates and reranking personalizes the final choice.

### Source of Truth and Vector Index Should Be Separate

SQLite and Pinecone serve different jobs:

```text
SQLite = durable facts and application state
Pinecone = semantic search index
```

This separation made the project easier to debug.

### Chunking Should Match the Data Shape

Fixed-size chunking is not always best. For book recommendation, a whole book profile is the natural chunk. This preserves title, author, summary, themes, source, and status together.

### Dense Retrieval Needs Metadata Filters

Dense retrieval is good at semantic similarity, but without filters it can mix categories. Module and status filters made retrieval much more accurate.

### Reranking Makes the System Explainable

The reranking layer made it possible to explain why a book was selected:

```text
retrieval score
module fit
candidate boost
source present
feedback penalties
rating pending
```

This is useful for demos and debugging.

### Feedback Is Part of the Product

The Yes / Maybe / No buttons are not just UI features. They create preference memory that future runs can use to avoid rejected books and adjust recommendations.

### Goodreads Ratings Need Care

Goodreads ratings change over time and were not reliably available from simple search. The schema supports ratings, but the current implementation leaves them pending unless verified. This is better than guessing.

## Current Status

Completed:

- SQLite schema
- Reading history ingestion
- Candidate book ingestion
- Chunking
- Pinecone integrated embedding/indexing
- Generated recommendation intents
- Filtered dense retrieval
- Reranking
- Weekly recommendation generation
- Markdown output
- Feedback logging
- Usage/evaluation logging
- Browser UI
- Semantic chat
- One-command weekly pipeline

Run the full pipeline:

```bash
cd /Users/roja/Documents/Agentic_AI/RAG
source .venv/bin/activate
python -m app.cli weekly
```

Run the UI:

```bash
python -m app.cli ui
```

Open:

```text
http://127.0.0.1:8765/
```

## Future Enhancements

- Add reliable Goodreads rating enrichment.
- Add automated online candidate discovery using Google Books, Open Library, or curated source APIs.
- Add LLM-based explanation generation while keeping outputs grounded.
- Add scheduled weekly automation.
- Add export to Notion, Google Sheets, or email.
- Add richer evaluation metrics based on long-term acceptance/rejection patterns.
