# Stage 1 API Implementation Plan

## Overview

This document outlines the complete plan for implementing the Stage 1 FastAPI endpoints for EasyHire Scout. This stage focuses on core functionality for job management, scraping operations, and basic search capabilities.

## Project Goals

- Build RESTful API endpoints for job scraping and management
- Enable job search and filtering capabilities
- Track scraping operations and errors
- Provide comprehensive job information in single API calls
- Establish a scalable architecture for future enhancements

---

## Key Decisions Made

### 1. **Rate Limiting**
- **Decision**: Not implemented in Stage 1
- **Rationale**: Focus on core functionality first, add rate limiting in later stages if needed

### 2. **Job Creation**
- **Decision**: `POST /api/v1/jobs` will handle related entities (skills, languages, categories) in one request
- **Rationale**: 
  - Jobs are primarily created by scraping services (which will use service layer directly)
  - POST endpoint useful for manual entry, testing, and future integrations
  - Single request reduces complexity for API consumers

### 3. **Soft Delete**
- **Decision**: Use soft delete (`is_active=False`) instead of hard delete
- **Rationale**: 
  - Preserves data integrity and history
  - Allows for job reactivation if needed
  - Better for analytics and auditing

### 4. **Search Implementation**
- **Decision**: Use simpler LIKE-based search for Stage 1
- **Rationale**: 
  - Easier to implement and understand
  - Sufficient for initial requirements
  - Can upgrade to PostgreSQL full-text search later (indexes already exist in schema)

### 5. **Response Format**
- **Decision**: Include all necessary related data (company, location, skills, languages, categories) in job responses
- **Rationale**: 
  - Reduces number of API calls needed
  - Better user experience
  - Single source of truth for job information

---

## API Structure & Priorities

### Priority 1: Core Functionality (Must Have)

#### 1. Jobs API
**Base Path**: `/api/v1/jobs`

| Method | Endpoint | Description | Priority |
|--------|----------|-------------|----------|
| GET | `/api/v1/jobs` | List jobs with filtering, pagination, search | HIGH |
| GET | `/api/v1/jobs/{job_id}` | Get job by ID with all related data | HIGH |
| POST | `/api/v1/jobs` | Create job (with nested skills, languages, categories) | HIGH |
| PATCH | `/api/v1/jobs/{job_id}` | Update job (soft delete via `is_active=False`) | HIGH |

**Query Parameters for GET `/api/v1/jobs`**:
- `page` (int, default: 1) - Page number
- `page_size` (int, default: 20) - Items per page
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

#### 2. Scraping Management API
**Base Path**: `/api/v1/scraping`

| Method | Endpoint | Description | Priority |
|--------|----------|-------------|----------|
| POST | `/api/v1/scraping/start` | Start a scraping run | HIGH |
| GET | `/api/v1/scraping/runs` | List scraping runs | HIGH |
| GET | `/api/v1/scraping/runs/{run_id}` | Get scraping run details | HIGH |
| GET | `/api/v1/scraping/runs/{run_id}/jobs` | Get jobs from a scraping run | HIGH |
| GET | `/api/v1/scraping/runs/{run_id}/errors` | Get errors from a scraping run | HIGH |

**Query Parameters for GET `/api/v1/scraping/runs`**:
- `status` (str, optional) - Filter by status: "running", "completed", "failed", "cancelled"
- `scrape_site_id` (int, optional) - Filter by scraping source
- `page` (int, default: 1) - Page number
- `page_size` (int, default: 20) - Items per page

**Request Body for POST `/api/v1/scraping/start`**:
```json
{
  "scrape_site_id": 1,
  "base_url": "https://example.com/jobs" // optional
}
```

### Priority 2: Supporting APIs (Nice to Have)

#### 3. Companies API
**Base Path**: `/api/v1/companies`

| Method | Endpoint | Description | Priority |
|--------|----------|-------------|----------|
| GET | `/api/v1/companies` | List companies | MEDIUM |
| GET | `/api/v1/companies/{company_id}` | Get company details | MEDIUM |

**Query Parameters for GET `/api/v1/companies`**:
- `page` (int, default: 1)
- `page_size` (int, default: 20)
- `search` (str, optional) - Search by company name

#### 4. Locations API
**Base Path**: `/api/v1/locations`

| Method | Endpoint | Description | Priority |
|--------|----------|-------------|----------|
| GET | `/api/v1/locations` | List locations | MEDIUM |
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
| GET | `/api/v1/skills` | List/search skills | MEDIUM |
| GET | `/api/v1/skills/{skill_id}` | Get skill details | MEDIUM |

**Query Parameters for GET `/api/v1/skills`**:
- `search` (str, optional) - Search by skill name
- `category` (str, optional) - Filter by category
- `page` (int, default: 1)
- `page_size` (int, default: 20)

### Priority 3: Reference APIs (Can Defer)

#### 6. Job Categories API
**Base Path**: `/api/v1/categories`

| Method | Endpoint | Description | Priority |
|--------|----------|-------------|----------|
| GET | `/api/v1/categories` | List all categories | LOW |

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
  "source_url": "https://example.com/jobs/12345",
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
      // Job object (same as above, but may exclude some nested details for list view)
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
│       ├── jobs.py        # Job endpoints
│       ├── companies.py   # Company endpoints
│       ├── locations.py   # Location endpoints
│       ├── skills.py      # Skills endpoints
│       ├── categories.py  # Category endpoints
│       └── scraping.py    # Scraping management endpoints
│
├── schemas/               # Pydantic models (request/response)
│   ├── __init__.py
│   ├── common.py          # Common schemas (pagination, responses)
│   ├── job.py             # Job request/response schemas
│   ├── company.py          # Company schemas
│   ├── location.py         # Location schemas
│   ├── skill.py            # Skill schemas
│   └── scraping.py        # Scraping schemas
│
└── services/              # Business logic layer
    ├── __init__.py
    ├── job_service.py     # Job business logic
    ├── company_service.py # Company business logic
    ├── location_service.py # Location business logic
    ├── skill_service.py   # Skill business logic
    └── scraping_service.py # Scraping business logic
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
   - Request schemas for validation
   - Response schemas for serialization
   - Common schemas (pagination, error responses)

2. **Services (Business Logic)**
   - Database queries
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
  - `201` - Created
  - `400` - Bad Request
  - `404` - Not Found
  - `500` - Internal Server Error

---

## Implementation Priority Order

### Phase 1: Foundation
1. Set up project structure (directories, `__init__.py` files)
2. Create common schemas (pagination, responses)
3. Set up FastAPI app instance with CORS
4. Create main router structure

### Phase 2: Core Jobs API
1. Create job schemas (request/response)
2. Implement job service (CRUD operations)
3. Implement job API routes
4. Test job endpoints

### Phase 3: Scraping API
1. Create scraping schemas
2. Implement scraping service
3. Implement scraping API routes
4. Test scraping endpoints

### Phase 4: Supporting APIs
1. Companies API (read-only)
2. Locations API (read-only)
3. Skills API (read-only)
4. Categories API (read-only)

### Phase 5: Testing & Refinement
1. Test all endpoints
2. Verify response formats
3. Test error handling
4. Performance testing (if needed)

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
- Allow override for admin views if needed

### Related Data Loading
- Use SQLAlchemy's `joinedload()` or `selectinload()` for eager loading
- Load company, location, skills, languages, categories in single query
- Avoid N+1 query problems

### Pagination
- Default: 20 items per page
- Maximum: 100 items per page (enforce limit)
- Calculate `total_pages` from `total` and `page_size`

---

## Next Steps

1. Review this plan
2. Set up project structure together
3. Implement Phase 1 (Foundation) together
4. Gradually implement remaining phases
5. Test and refine as we go

---

## Questions for Future Consideration

- Authentication/Authorization (not needed for Stage 1)
- Rate limiting (deferred)
- Caching strategy (for future optimization)
- API versioning strategy (currently v1)
- Webhook support for scraping completion (future feature)

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Status**: Planning Complete - Ready for Implementation
