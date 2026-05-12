# Stage 1 API Implementation Plan (Version 3.1)

## Overview

This document outlines the complete plan for implementing the Stage 1 FastAPI endpoints for EasyHire Scout. **EasyHire Scout is a job scraper bot** that leverages AI to discover, extract, and categorize job postings from major sites based on user-defined search criteria.

The API focuses on:
- **Configuring and executing scraping runs** with specific search criteria.
- **Viewing scraped jobs** with advanced FTS (Full-Text Search) ranking.
- **Tracking scraping operations** through a persistent distributed task queue.

**Guiding Principle**: Jobs are **exclusively created by the scraping bot**. The API is a window into the discovered data and a control panel for the scraper.

---

## Key Decisions Made (Architectural Refined)

### 1. **Background Execution & Monitoring**
- **Decision**: Use **Celery** with **Redis** and **Database State Monitoring**.
- **WHY**: 
  - **Persistence**: Scraping and LLM tasks are resource-heavy; Celery ensures tasks aren't lost on server restarts.
  - **Fault Tolerance**: Automatic retries handle flaky site connections and LLM timeouts.
  - **Monitoring**: Integration with Flower for real-time visibility.

### 2. **Success-Triggered Differential Inactivation (The 2-Run Rule)**
- **Decision**: Use **Cohort-Scoped Success-Triggered Inactivation**.
- **WHY**: 
  - **The 2-Run Rule**: A job is marked `is_active=False` only if it has been missing for **two consecutive successful runs**. This prevents accidental deletion due to "partial scrapes".
  - **Success Trigger**: Inactivation only runs if the `ScrapeRun` status is `completed` AND `jobs_found > 0`.
  - **Cohort Management**: Targets only jobs within the same `SearchCriteria` (site + role + location).

### 3. **Platform-Wide Linguistic Search (PostgreSQL FTS)**
- **Decision**: PostgreSQL Full-Text Search (FTS) with `ts_rank` + GIN Indexes.
- **WHY**: 
  - **Strict Deprecation of LIKE**: `LIKE/ILIKE` is deprecated across the entire platform (Jobs, Companies, Skills).
  - **Ranking**: Uses `ts_rank` to provide relevance-based results (e.g., matching "Python" in title ranks higher than description).

### 4. **Canonical Hashing Protocol (Cohort Resolution)**
- **Decision**: Generate a `cohort_hash` via a 4-step canonicalization pipeline.
- **WHY**: Ensures that permutations like `["Python", "FastAPI"]` vs `["FastAPI", "python"]` resolve to the same intent, preventing duplicate scraping runs and data fragmentation.

### 5. **Double-Headed Language Extraction**
- **Decision**: LLM extracts both `content_language` (the text) and `requirement_language` (mandated skills).
- **WHY**: Prevents false negatives where an English-written job post actually requires German fluency.

### 6. **Skill Canonicalization**
- **Decision**: Use a **Service-Layer Matcher** to map raw strings to stable IDs.
- **WHY**: Maps variants like "JS" and "Javascript" to the same canonical "JavaScript" ID, making filters highly reliable.

---

## API Structure & Priorities

### Priority 1: Scraping Management API (`/api/v1/scraping`)

| Method | Endpoint | Description | Priority |
|--------|----------|-------------|----------|
| POST | `/api/v1/scraping/start` | Start a scraping run (triggers Canonical Hashing) | HIGH |
| GET | `/api/v1/scraping/runs` | List runs with status & cohort filtering | HIGH |
| GET | `/api/v1/scraping/runs/{id}` | Get run details, stats, and warnings | HIGH |
| GET | `/api/v1/scraping/runs/{id}/jobs`| Get jobs discovered by a specific run | HIGH |
| GET | `/api/v1/scraping/sites` | List available scraping sources (LinkedIn, etc.) | HIGH |

### Priority 2: Jobs API (`/api/v1/jobs`)

| Method | Endpoint | Description | Priority |
|--------|----------|-------------|----------|
| GET | `/api/v1/jobs` | List jobs with **FTS Ranking** and filtering | HIGH |
| GET | `/api/v1/jobs/{job_id}` | Get job by ID with all canonicalized data | HIGH |

---

## Response Body Examples

### Job Detail Response (GET `/api/v1/jobs/{job_id}`)
```json
{
  "id": 1,
  "title": "Senior Python Developer",
  "description": "Full description here...",
  "external_id": "linkedin-12345",
  "content_language": "English",
  "requirement_language": ["German", "English"],
  "is_active": true,
  "last_seen_at": "2024-01-15T10:00:00Z",
  "missing_count": 0,
  "years_min": 5,
  "company": {
    "id": 5,
    "name": "Tech Corp",
    "industry": "Technology"
  },
  "location": {
    "id": 10,
    "city": "Berlin",
    "country": "Germany",
    "remote": false
  },
  "skills": [
    { "id": 1, "name": "Python", "category": "Language" },
    { "id": 2, "name": "FastAPI", "category": "Framework" }
  ],
  "scrape_run": {
    "id": 42,
    "status": "completed",
    "completed_at": "2024-01-15T11:00:00Z"
  }
}
```

### Scraping Run Detail (GET `/api/v1/scraping/runs/{run_id}`)
```json
{
  "id": 42,
  "cohort_hash": "a1b2c3d4e5f6...",
  "status": "completed",
  "jobs_found": 150,
  "jobs_saved": 145,
  "started_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T11:30:00Z",
  "search_criteria": {
    "job_role": "Python Developer",
    "location": "Germany",
    "scrape_site": "LinkedIn"
  },
  "warnings": ["Rate limited at 10:45 AM", "2 duplicate jobs found"]
}
```

---

## Project File Structure (Modular & Reusable)

```
easyhire_scout/
├── api/                   # API Routing Layer
│   ├── main.py            # App Entry Point
│   └── v1/                # Versioned Endpoints
│       ├── jobs.py        # Job retrieval with FTS ranking
│       ├── scraping.py    # Scraping control & run monitoring
│       ├── companies.py   # Company directory (FTS enabled)
│       ├── locations.py   # Location directory
│       ├── skills.py      # Skill directory (FTS enabled)
│       └── categories.py  # Category management
│
├── services/              # Business Logic (Reusable Methods)
│   ├── job_service.py     # Complex FTS queries & lifecycle logic
│   ├── scraping_service.py # Run creation, Hashing, & Inactivation logic
│   ├── skill_matcher.py   # AI-to-DB Skill mapping & canonicalization
│   ├── company_service.py # Company deduplication & enrichment
│   ├── location_service.py # Geo-normalization & remote logic
│   └── category_service.py # Industry & Role classification
│
├── schemas/               # Pydantic (Data Validation & Serialization)
│   ├── common.py          # Pagination, Sorting & Error schemas
│   ├── job.py             # Job request/response shapes
│   ├── scraping.py        # Search criteria & Run shapes
│   └── skill.py           # Skill, Variant & Category shapes
│
├── models.py              # SQLAlchemy Core Models (FTS & Freshness columns)
└── database.py            # Session & Engine management
```

---

## Technical Notes for Development

### 1. The Canonical Hashing Pipeline
Before creating a `SearchCriteria` record, execute:
1. **Scalar Normalization**: Lowercase/strip `job_role`, `location`, `language`.
2. **Array Normalization**: Lowercase, deduplicate, and **alphabetically sort** `skills`.
3. **Hashing**: SHA-256 of the resulting deterministic JSON string.

### 2. Differential Inactivation Logic
After a successful run (`completed` status + `jobs_found > 0`):
1. Update `last_seen_at` for all found jobs.
2. For jobs in the same `cohort_hash` where `last_seen_at < run.started_at`:
   - Increment `missing_count`.
   - If `missing_count >= 2`, set `is_active = FALSE`.

### 3. Search ranking (FTS)
Always sort list endpoints by relevancy unless an explicit sort is provided:
```python
query = query.order_by(func.ts_rank(Job.fts_vector, func.plainto_tsquery(q)).desc())
```

---

**Document Version**: 3.1  
**Last Updated**: 2026-05-12  
**Status**: Finalized for Implementation  
**Key Change**: Restored full service architecture and detailed response bodies updated for architectural alignment.
