# Stage 1 API Implementation Plan

## Overview

This document outlines the complete plan for implementing the Stage 1 FastAPI endpoints for EasyHire Scout. **EasyHire Scout is a job scraper bot** that scrapes jobs from major job posting sites based on user-defined search criteria (role, language, location, strictness). The API in Stage 1 focuses on:

- **Configuring and executing scraping runs** with specific search criteria
- **Viewing scraped jobs** (read-only access to jobs discovered by the scraper)
- **Tracking scraping operations** and errors
- **Providing comprehensive job information** in single API calls

**Important**: Jobs are **only created by the scraping bot** - there are no manual job creation endpoints. The API is primarily for configuring scrapes and viewing scraped results.

---

## Project Goals

- Build RESTful API endpoints for **scraping configuration and execution**
- Enable **read-only access** to scraped jobs with filtering and search capabilities
- Track scraping operations, runs, and errors
- Provide comprehensive job information (with related entities) in single API calls
- Establish a scalable architecture for future enhancements (e.g., resume matching, job recommendations)

---

## Key Decisions Made

### 1. **Rate Limiting**
- **Decision**: Not implemented in Stage 1.0.1
- **Rationale**: Focus on core functionality first, add rate limiting in later sub-stages if needed

### 2. **Job Creation**
- **Decision**: Jobs are **only created by the scraping bot** - no public `POST /api/v1/jobs` endpoint
- **Rationale**: 
  - This is a scraper bot, not a general job board
  - Jobs come exclusively from scraping operations
  - Scraping services will use the service layer directly (not via API)
  - Manual job entry/testing can be done via database or admin tools (not Stage 1 scope)

### 3. **Scraping Configuration**
- **Decision**: `POST /api/v1/scraping/start` accepts detailed search criteria (role, language, location, strictness)
- **Rationale**:
  - Users need to configure what jobs to scrape
  - Search criteria determine which jobs are discovered and stored
  - Language strictness allows filtering (e.g., "strictly English" means only English-language jobs)

### 4. **Soft Delete**
- **Decision**: Use soft delete (`is_active=False`) instead of hard delete
- **Rationale**: 
  - Preserves data integrity and scraping history
  - Allows for job reactivation if needed
  - Better for analytics and auditing
  - Jobs can be marked inactive when they expire or are removed from source sites

### 5. **Search Implementation**
- **Decision**: Use simpler LIKE-based search for Stage 1
- **Rationale**: 
  - Easier to implement and understand
  - Sufficient for initial requirements
  - Can upgrade to PostgreSQL full-text search later (indexes already exist in schema)

### 6. **Response Format**
- **Decision**: Include all necessary related data (company, location, skills, languages, categories) in job responses
- **Rationale**: 
  - Reduces number of API calls needed
  - Better user experience
  - Single source of truth for job information

---

## API Structure & Priorities

### Priority 1: Scraping Configuration & Execution (Must Have)

#### 1. Scraping Management API
**Base Path**: `/api/v1/scraping`

| Method | Endpoint | Description | Priority |
|--------|----------|-------------|----------|
| POST | `/api/v1/scraping/start` | Start a scraping run with search criteria | HIGH |
| GET | `/api/v1/scraping/runs` | List scraping runs with filtering | HIGH |
| GET | `/api/v1/scraping/runs/{run_id}` | Get scraping run details | HIGH |
| GET | `/api/v1/scraping/runs/{run_id}/jobs` | Get jobs from a specific scraping run | HIGH |
| GET | `/api/v1/scraping/runs/{run_id}/errors` | Get errors from a scraping run | HIGH |

**Query Parameters for GET `/api/v1/scraping/runs`**:
- `status` (str, optional) - Filter by status: "running", "completed", "failed", "cancelled"
- `scrape_site_id` (int, optional) - Filter by scraping source (e.g., LinkedIn, Indeed)
- `page` (int, default: 1) - Page number
- `page_size` (int, default: 20) - Items per page

**Request Body for POST `/api/v1/scraping/start`**:
```json
{
  "scrape_site_id": 1,
  "job_role": "Python Developer",
  "location": "Germany",
  "language": "English",
  "language_strict": true,
  "additional_filters": {
    "years_min": 3,
    "years_max": 10,
    "job_type": "full_time"
  }
}
```

**Fields**:
- `scrape_site_id` (int, required) - Which job site to scrape (e.g., LinkedIn, Indeed, Stack Overflow Jobs)
- `job_role` (str, required) - The job role/title to search for (e.g., "Python Developer", "Data Scientist")
- `location` (str, required) - Location to search in (e.g., "Germany", "Berlin", "Remote")
- `language` (str, required) - Language requirement (e.g., "English", "German")
- `language_strict` (bool, required) - If `true`, only return jobs strictly in the specified language; if `false`, include jobs that may have mixed languages
- `additional_filters` (object, optional) - Additional search criteria:
  - `years_min` (int, optional) - Minimum years of experience
  - `years_max` (int, optional) - Maximum years of experience
  - `job_type` (str, optional) - Job type filter (e.g., "full_time", "part_time", "contract")
  - `remote` (bool, optional) - Filter for remote jobs only

**Response for POST `/api/v1/scraping/start`**:
```json
{
  "run_id": 42,
  "status": "running",
  "scrape_site": {
    "id": 1,
    "name": "LinkedIn",
    "base_url": "https://linkedin.com/jobs"
  },
  "search_criteria": {
    "job_role": "Python Developer",
    "location": "Germany",
    "language": "English",
    "language_strict": true
  },
  "started_at": "2024-01-15T10:00:00Z",
  "message": "Scraping run started successfully"
}
```

### Priority 2: Jobs API (Read-Only - Must Have)

#### 2. Jobs API
**Base Path**: `/api/v1/jobs`

| Method | Endpoint | Description | Priority |
|--------|----------|-------------|----------|
| GET | `/api/v1/jobs` | List scraped jobs with filtering, pagination, search | HIGH |
| GET | `/api/v1/jobs/{job_id}` | Get job by ID with all related data | HIGH |

**Note**: There are **no POST or PATCH endpoints** for jobs. Jobs are only created by the scraping bot.

**Query Parameters for GET `/api/v1/jobs`**:
- `page` (int, default: 1) - Page number
- `page_size` (int, default: 20) - Items per page (max 100)
- `company_id` (int, optional) - Filter by company
- `location_id` (int, optional) - Filter by location
- `category_id` (int, optional) - Filter by category
- `skill_ids[]` (list[int], optional) - Filter by skills (array)
- `years_min` (int, optional) - Minimum years of experience
- `years_max` (int, optional) - Maximum years of experience
- `requires_german` (bool, optional) - Filter by German requirement
- `job_type` (str, optional) - Filter by job type (e.g., "full_time", "part_time")
- `is_active` (bool, optional, default: true) - Filter by active status
- `search` (str, optional) - LIKE-based search on title/description
- `posted_after` (datetime, optional) - Filter by posted date (after)
- `posted_before` (datetime, optional) - Filter by posted date (before)
- `scrape_run_id` (int, optional) - Filter by scraping run that discovered this job
- `scrape_site_id` (int, optional) - Filter by source site (e.g., LinkedIn, Indeed)

### Priority 3: Supporting APIs (Nice to Have)

#### 3. Companies API
**Base Path**: `/api/v1/companies`

| Method | Endpoint | Description | Priority |
|--------|----------|-------------|----------|
| GET | `/api/v1/companies` | List companies (discovered from scraped jobs) | MEDIUM |
| GET | `/api/v1/companies/{company_id}` | Get company details | MEDIUM |

**Query Parameters for GET `/api/v1/companies`**:
- `page` (int, default: 1)
- `page_size` (int, default: 20)
- `search` (str, optional) - Search by company name

#### 4. Locations API
**Base Path**: `/api/v1/locations`

| Method | Endpoint | Description | Priority |
|--------|----------|-------------|----------|
| GET | `/api/v1/locations` | List locations (from scraped jobs) | MEDIUM |
| GET | `/api/v1/locations/{location_id}` | Get location details | MEDIUM |

**Query Parameters for GET `/api/v1/locations`**:
- `country` (str, optional) - Filter by country
- `city` (str, optional) - Filter by city
- `region` (str, optional) - Filter by region
- `remote` (bool, optional) - Filter by remote status
- `page` (int, default: 1)
- `page_size` (int, default: 20)

#### 5. Skills API
**Base Path**: `/api/v1/skills`

| Method | Endpoint | Description | Priority |
|--------|----------|-------------|----------|
| GET | `/api/v1/skills` | List/search skills (extracted from scraped jobs) | MEDIUM |
| GET | `/api/v1/skills/{skill_id}` | Get skill details | MEDIUM |

**Query Parameters for GET `/api/v1/skills`**:
- `search` (str, optional) - Search by skill name
- `category` (str, optional) - Filter by category
- `page` (int, default: 1)
- `page_size` (int, default: 20)

### Priority 4: Reference APIs (Can Defer)

#### 6. Job Categories API
**Base Path**: `/api/v1/categories`

| Method | Endpoint | Description | Priority |
|--------|----------|-------------|----------|
| GET | `/api/v1/categories` | List all categories | LOW |

#### 7. Scrape Sites API
**Base Path**: `/api/v1/scrape-sites`

| Method | Endpoint | Description | Priority |
|--------|----------|-------------|----------|
| GET | `/api/v1/scrape-sites` | List available scraping sources (LinkedIn, Indeed, etc.) | LOW |

---

## Response Format Examples

### Job Response (GET `/api/v1/jobs/{job_id}`)
```json
{
  "id": 1,
  "title": "Senior Python Developer",
  "normalized_title": "senior python developer",
  "description": "We are looking for an experienced Python developer...",
  "requirements": "5+ years of Python experience...",
  "responsibilities": "Design and implement backend services...",
  "external_id": "job-12345",
  "years_min": 5,
  "years_max": 8,
  "years_overall": false,
  "salary_min": 70000.00,
  "salary_max": 90000.00,
  "salary_currency": "EUR",
  "job_type": "full_time",
  "employment_type": "permanent",
  "requires_german": true,
  "posted_date": "2024-01-15T10:00:00Z",
  "scraped_at": "2024-01-15T11:30:00Z",
  "source_url": "https://linkedin.com/jobs/view/12345",
  "is_active": true,
  "is_duplicate": false,
  "created_at": "2024-01-15T11:30:00Z",
  "updated_at": "2024-01-15T11:30:00Z",
  "company": {
    "id": 5,
    "name": "Tech Corp",
    "normalized_name": "tech corp",
    "website": "https://techcorp.com",
    "careers_url": "https://techcorp.com/careers",
    "industry": "Technology",
    "company_size": "51-200",
    "founded_year": 2015
  },
  "location": {
    "id": 10,
    "city": "Berlin",
    "country": "Germany",
    "region": "Berlin",
    "remote": false,
    "latitude": 52.5200,
    "longitude": 13.4050
  },
  "skills": [
    {
      "id": 1,
      "canonical_name": "Python",
      "category": "programming_language",
      "weight": 1.0
    },
    {
      "id": 2,
      "canonical_name": "FastAPI",
      "category": "framework",
      "weight": 0.7
    }
  ],
  "languages": [
    {
      "language": "English",
      "requirement_level": "required"
    },
    {
      "language": "German",
      "requirement_level": "preferred"
    }
  ],
  "categories": [
    {
      "id": 1,
      "name": "backend"
    }
  ],
  "scrape_run": {
    "id": 42,
    "scrape_site_id": 1,
    "started_at": "2024-01-15T10:00:00Z",
    "completed_at": "2024-01-15T11:30:00Z",
    "status": "completed",
    "jobs_found": 150,
    "jobs_saved": 145
  },
  "source_site": {
    "id": 1,
    "name": "LinkedIn",
    "base_url": "https://linkedin.com/jobs"
  }
}
```

### Paginated Response (GET `/api/v1/jobs`)
```json
{
  "items": [
    {
      // Job object (same structure as above, but may exclude some nested details for list view)
    }
  ],
  "total": 1250,
  "page": 1,
  "page_size": 20,
  "total_pages": 63
}
```

### Scraping Run Response (GET `/api/v1/scraping/runs/{run_id}`)
```json
{
  "id": 42,
  "scrape_site_id": 1,
  "scrape_site": {
    "id": 1,
    "name": "LinkedIn",
    "base_url": "https://linkedin.com/jobs"
  },
  "search_criteria": {
    "job_role": "Python Developer",
    "location": "Germany",
    "language": "English",
    "language_strict": true,
    "additional_filters": {
      "years_min": 3,
      "job_type": "full_time"
    }
  },
  "started_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T11:30:00Z",
  "status": "completed",
  "jobs_found": 150,
  "jobs_saved": 145,
  "warnings": [
    "Some jobs had missing salary information",
    "5 duplicate jobs detected"
  ],
  "created_at": "2024-01-15T10:00:00Z"
}
```

---

## Project File Structure

```
easyhire_scout/
├── __init__.py
├── models.py              # SQLAlchemy models (existing)
├── database.py            # DB connection (existing)
│
├── api/                   # API routes/endpoints
│   ├── __init__.py
│   ├── main.py            # FastAPI app instance
│   └── v1/                # API versioning
│       ├── __init__.py
│       ├── router.py      # Main router (includes all routes)
│       ├── jobs.py        # Job endpoints (read-only)
│       ├── companies.py   # Company endpoints (read-only)
│       ├── locations.py   # Location endpoints (read-only)
│       ├── skills.py      # Skills endpoints (read-only)
│       ├── categories.py  # Category endpoints (read-only)
│       ├── scraping.py    # Scraping management endpoints
│       └── scrape_sites.py # Scrape sites endpoints (read-only)
│
├── schemas/               # Pydantic models (request/response)
│   ├── __init__.py
│   ├── common.py          # Common schemas (pagination, responses)
│   ├── job.py             # Job response schemas (no request schemas for creation)
│   ├── company.py         # Company schemas
│   ├── location.py        # Location schemas
│   ├── skill.py           # Skill schemas
│   └── scraping.py        # Scraping request/response schemas
│
└── services/              # Business logic layer
    ├── __init__.py
    ├── job_service.py     # Job business logic (read operations)
    ├── company_service.py # Company business logic (read operations)
    ├── location_service.py # Location business logic (read operations)
    ├── skill_service.py   # Skill business logic (read operations)
    └── scraping_service.py # Scraping business logic (create runs, track status)
```

---

## Implementation Approach

### Architecture Pattern
- **Layered Architecture**: API → Services → Database
- **Separation of Concerns**: 
  - API routes handle HTTP requests/responses
  - Services contain business logic
  - Models represent database entities
  - Schemas handle validation and serialization

### Key Components

1. **Schemas (Pydantic Models)**
   - Request schemas for scraping configuration validation
   - Response schemas for serialization (jobs, scraping runs, etc.)
   - Common schemas (pagination, error responses)
   - **Note**: No job creation request schemas (jobs created by scraper only)

2. **Services (Business Logic)**
   - Database queries (read operations for jobs, companies, etc.)
   - Scraping run management (create runs, update status, track progress)
   - Data transformation
   - Business rules
   - Error handling

3. **API Routes (FastAPI Endpoints)**
   - HTTP method handlers
   - Request validation
   - Response formatting
   - Dependency injection (database sessions)

### Database Session Management
- Use `get_db()` dependency from `easyhire_scout.database`
- Sessions are automatically closed after request
- Example: `db: Session = Depends(get_db)`

### Error Handling
- Use FastAPI's HTTPException for errors
- Standard error response format:
  ```json
  {
    "detail": "Error message here"
  }
  ```
- Common HTTP status codes:
  - `200` - Success
  - `201` - Created (for scraping run creation)
  - `400` - Bad Request
  - `404` - Not Found
  - `500` - Internal Server Error

---

## Implementation Priority Order

### Phase 1: Foundation ✅ (Completed)
1. ✅ Set up project structure (directories, `__init__.py` files)
2. ✅ Create common schemas (pagination, responses)
3. ✅ Set up FastAPI app instance with CORS
4. ✅ Create main router structure

### Phase 2: Scraping API (Priority 1)
1. Create scraping schemas (request for `POST /scraping/start`, response for runs)
2. Implement scraping service:
   - Create scraping run record
   - Update run status
   - Track jobs found/saved
   - Handle errors
3. Implement scraping API routes:
   - `POST /api/v1/scraping/start` - Accept search criteria, create run, trigger scraper (async)
   - `GET /api/v1/scraping/runs` - List runs with filtering
   - `GET /api/v1/scraping/runs/{run_id}` - Get run details
   - `GET /api/v1/scraping/runs/{run_id}/jobs` - Get jobs from run
   - `GET /api/v1/scraping/runs/{run_id}/errors` - Get errors from run
4. Test scraping endpoints

**Note**: The actual scraping logic (web scraping, parsing, etc.) is **not** part of Stage 1 API implementation. The API will:
- Accept scraping configuration
- Create a `ScrapeRun` record
- Return immediately with `status: "running"`
- The scraping bot/service (separate component) will update the run status and create job records

### Phase 3: Jobs API (Priority 2 - Read-Only)
1. Create job response schemas (no request schemas for creation)
2. Implement job service (read operations only):
   - List jobs with filtering, pagination, search
   - Get job by ID with all related data
   - Filter by scrape run, scrape site, etc.
3. Implement job API routes:
   - `GET /api/v1/jobs` - List jobs with query parameters
   - `GET /api/v1/jobs/{job_id}` - Get job details
4. Test job endpoints

### Phase 4: Supporting APIs (Priority 3)
1. Companies API (read-only)
2. Locations API (read-only)
3. Skills API (read-only)
4. Categories API (read-only)
5. Scrape Sites API (read-only)

### Phase 5: Testing & Refinement
1. Test all endpoints
2. Verify response formats
3. Test error handling
4. Performance testing (if needed)
5. Integration testing with scraping bot (when available)

---

## Technical Notes

### Search Implementation (LIKE-based)
- Use SQLAlchemy's `ilike()` for case-insensitive search
- Search on: `title`, `description`, `requirements`
- Example query:
  ```python
  query = query.filter(
      or_(
          Job.title.ilike(f"%{search_term}%"),
          Job.description.ilike(f"%{search_term}%"),
          Job.requirements.ilike(f"%{search_term}%")
      )
  )
  ```

### Soft Delete Implementation
- Update `is_active=False` instead of deleting
- Filter queries by default: `query.filter(Job.is_active == True)`
- Allow override for admin views if needed (via `is_active` query parameter)

### Related Data Loading
- Use SQLAlchemy's `joinedload()` or `selectinload()` for eager loading
- Load company, location, skills, languages, categories in single query
- Avoid N+1 query problems
- Example:
  ```python
  query = query.options(
      joinedload(Job.company),
      joinedload(Job.location),
      selectinload(Job.skills),
      selectinload(Job.languages),
      selectinload(Job.categories)
  )
  ```

### Pagination
- Default: 20 items per page
- Maximum: 100 items per page (enforce limit)
- Calculate `total_pages` from `total` and `page_size`
- Use `PaginationParams` schema from `common.py`

### Scraping Run Status Management
- Status values: `"running"`, `"completed"`, `"failed"`, `"cancelled"`
- When `POST /scraping/start` is called:
  1. Create `ScrapeRun` record with `status="running"`
  2. Store search criteria (may need to extend `scrape_runs` table or store as JSON)
  3. Return immediately with run ID
  4. Actual scraping happens asynchronously (separate service/worker)
  5. Scraping service updates run status and creates job records

---

## Next Steps

1. ✅ Review this plan
2. ✅ Set up project structure together
3. ✅ Implement Phase 1 (Foundation) together
4. **Next**: Implement Phase 2 (Scraping API) together
5. Gradually implement remaining phases
6. Test and refine as we go

---

## Questions for Future Consideration

- **Authentication/Authorization**: Not needed for Stage 1, but will be needed for production
- **Rate Limiting**: Deferred to later stages
- **Caching Strategy**: For future optimization (e.g., cache company/location lookups)
- **API Versioning Strategy**: Currently v1, plan for future versions
- **Webhook Support**: For scraping completion notifications (future feature)
- **Scraping Bot Integration**: The actual scraping logic is a separate component that will:
  - Read scraping run configuration from database
  - Execute web scraping
  - Create job records via service layer
  - Update scraping run status
  - Log errors to `scrape_errors` table
- **Language Strictness Logic**: How to determine if a job is "strictly" in a language (may require NLP/LLM analysis in future stages)

---

**Document Version**: 2.0  
**Last Updated**: 2024  
**Status**: Planning Complete - Ready for Implementation  
**Key Change**: Revised to reflect job scraper bot architecture (jobs only created by scraping, no manual job creation endpoints)
