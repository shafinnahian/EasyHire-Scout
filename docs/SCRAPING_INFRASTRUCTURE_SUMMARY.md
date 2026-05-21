# Scraping Infrastructure & Background Execution Summary

This document summarizes the complete setup for the background execution system, the Docker orchestration, and the Canonical Hashing Protocol implemented for Stage 1.

## 1. Architectural Foundation (Docker)
The system is now fully containerized to ensure environment consistency and easy management of background services.

| Service | Technology | Role |
|:---|:---|:---|
| **API** | FastAPI | Main entry point and documentation. |
| **Worker** | Celery | Executes long-running scraping and AI tasks. |
| **Broker** | Redis | Message carrier between API and Worker. |
| **Database** | PostgreSQL 16 | Persistent storage for jobs, runs, and cohorts. |
| **Monitor** | Flower | Real-time UI for task status and debugging. |

## 2. The Service Layer (Reusable Logic)
Following industrial best practices, the business logic is decoupled from the API routes into a standalone **Service Layer**.

### **HashingService**
Implements the **Canonical Hashing Protocol**.
- **Normalization**: Lowercases and strips all search strings.
- **Determinism**: Recursively sorts lists (like skills) and dictionary keys.
- **Uniqueness**: Generates a SHA-256 `cohort_hash` from the canonical data.
- **Benefit**: Ensures that permutations like `["Python", "FastAPI"]` vs `["FastAPI", "python"]` are recognized as the same search intent.

### **ScrapingService**
Orchestrates the lifecycle of scraping runs.
- **Cohort Resolution**: Uses the `HashingService` to find or create a `SearchCriteria` entry (the "Cohort").
- **State Management**: Updates the database status (`running`, `completed`, `failed`) and tracks job counts.
- **Decoupling**: Can be called by API routes, CLI tools, or Cron jobs without duplicating logic.

## 3. Database & Models
- **`search_criteria`**: An immutable log of unique search intents, identified by `cohort_hash`.
- **`scrape_runs`**: Linked to a cohort, tracking the history and success of individual executions.
- **`jobs`**: Tagged with both `scrape_run_id` and `search_criteria_id` for advanced filtering and inactivation logic.

## 4. How to Use & Monitor

### Accessing the System
- **API Documentation**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **Task Monitoring (Flower)**: [http://localhost:5555](http://localhost:5555)

### Running the System
```bash
# Start everything
docker compose up -d

# View logs
docker compose logs -f

# Rebuild after code changes
docker compose up --build -d
```

### Triggering a Scrape
Send a POST request to `/api/v1/scraping/start`. The API will:
1. Generate the `cohort_hash`.
2. Resolve the `SearchCriteria` ID.
3. Create a `ScrapeRun` record.
4. Hand off the actual work to the Celery worker.
5. Return a `201 Created` with the `run_id` immediately.
