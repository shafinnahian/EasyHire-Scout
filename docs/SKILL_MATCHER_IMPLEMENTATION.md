# Skill Matcher Service - Implementation Documentation

## Overview

The Skill Matcher Service is a three-tier hybrid matching system that maps raw skill strings to canonical skill IDs in the database. It minimizes DeepSeek API costs while maintaining high accuracy.

## Architecture

```
Raw Skill Input → Tier 1 (Exact) → Tier 2 (Fuzzy) → Tier 3 (LLM) → Canonical Skill ID
                     ↓ 80%           ↓ 15%           ↓ 5%
                   <1ms/free       <10ms/free      <2s/paid
```

### Three-Tier Matching Strategy

1. **Tier 1: Exact Match** (O(1), <1ms)
   - Normalized string lookup against canonical names
   - Checks SkillVariant table for known aliases
   - Confidence: 1.0 (canonical) or 0.95 (variant)

2. **Tier 2: Fuzzy Match** (O(n), <10ms)
   - RapidFuzz token_set_ratio algorithm
   - Handles typos, word order variations
   - Threshold: 85/100 minimum score
   - Confidence: 0.85-0.90 based on score

3. **Tier 3: LLM Match** (O(API_latency), <2s)
   - DeepSeek API for semantic matching
   - Only called if Tier 1 & 2 fail
   - Confidence: 0.70-1.0 from LLM response
   - Automatic retry with exponential backoff

## File Structure

```
easyhire_scout/
├── skills/                          # Feature module
│   ├── __init__.py                  # Public API
│   ├── skill_matcher.py             # Main service (3-tier logic)
│   ├── skill_normalizer.py          # Text normalization
│   ├── llm_client.py                # DeepSeek API wrapper
│   ├── exceptions.py                # Typed error hierarchy
│   └── schemas.py                   # Pydantic schemas
├── tasks/
│   └── skill_processing_tasks.py    # Celery batch processor
├── core/
│   └── config.py                    # LLM configuration
└── scripts/
    └── seed_skills.py               # Seed 60+ skills with variants
```

## Configuration

### Environment Variables (.env)

```env
# Required
DEEPSEEK_API_KEY=sk-your-actual-key-here

# Optional (with defaults)
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=30
DEEPSEEK_MAX_RETRIES=3
ENABLE_LLM_MATCHING=true
```

### Security Best Practices

✅ API key loaded from `.env` via Pydantic validation  
✅ App crashes at startup if key missing (fail fast)  
✅ `.env` in `.gitignore`, `.env.example` committed  
✅ Type-safe access via `settings.DEEPSEEK_API_KEY`  

## Installation

### 1. Install Dependencies

```bash
# Install package with new dependencies
pip install .

# Or install in development mode
pip install -e .
```

New dependencies added:
- `rapidfuzz>=3.0.0` - Fast fuzzy string matching
- `tenacity>=8.0.0` - Retry logic with exponential backoff

### 2. Configure Environment

```bash
# Copy example and add your API key
cp .env.example .env
nano .env  # Add your DEEPSEEK_API_KEY
```

### 3. Seed Skills Database

```bash
# Run seed script to populate skills
python scripts/seed_skills.py
```

This seeds 60+ core tech skills across categories:
- Programming Languages (Python, JavaScript, Java, Go, etc.)
- Frameworks (React, Django, FastAPI, Spring Boot, etc.)
- Databases (PostgreSQL, MongoDB, Redis, etc.)
- Cloud (AWS, GCP, Azure)
- DevOps (Docker, Kubernetes, CI/CD, etc.)

## Usage

### Basic Usage

```python
from sqlalchemy.orm import Session
from easyhire_scout.skills import SkillMatcherService

# Match single skill
results = SkillMatcherService.match_skills(
    db=db,
    raw_skills=["Python", "React.js", "ML"],
    use_llm=True
)

for result in results:
    print(f"{result.raw_input} -> {result.skill_name}")
    print(f"  Confidence: {result.confidence}")
    print(f"  Tier: {result.tier_used}")
    print(f"  Needs review: {result.needs_review}")
```

### Background Processing (Celery)

```python
from easyhire_scout.tasks.skill_processing_tasks import process_skill_batch

# Queue batch processing
task = process_skill_batch.delay(
    raw_skills=["Python", "React.js", "ML"],
    use_llm=True
)

# Get result
result = task.get(timeout=60)
print(result["stats"])
```

### Skill Extraction from Job Description

```python
from easyhire_scout.tasks.skill_processing_tasks import extract_and_match_skills

# Extract and match skills from job posting
task = extract_and_match_skills.delay(
    job_id=123,
    job_title="Senior Python Developer",
    job_description="We need Python, Django, PostgreSQL...",
    requirements="5+ years Python, Docker, AWS"
)

result = task.get()
print(f"Extracted: {result['extracted_skills']}")
print(f"Matched: {result['matched_skills']}")
```

## API Reference

### SkillMatcherService

#### `match_skills(db, raw_skills, use_llm=True)`

Match multiple raw skill strings to canonical skills.

**Parameters:**
- `db` (Session): Database session
- `raw_skills` (List[str]): List of raw skill strings
- `use_llm` (bool): Whether to use LLM for Tier 3 (default: True)

**Returns:**
- `List[MatchResult]`: Match results with confidence scores

**Example:**
```python
results = SkillMatcherService.match_skills(
    db=db,
    raw_skills=["JS", "React.js", "PostgreSQL"],
    use_llm=True
)
```

### DeepSeekClient

#### `match_skill(raw_skill, candidate_skills)`

Ask LLM to match raw skill to one of the candidates.

**Parameters:**
- `raw_skill` (str): Raw skill string to match
- `candidate_skills` (List[str]): List of canonical skill names

**Returns:**
- `LLMMatchResponse`: Matched skill, confidence, and reasoning

**Raises:**
- `LLMAPIError`: API returned error status
- `LLMTimeoutError`: Request timed out

**Example:**
```python
client = DeepSeekClient()
response = client.match_skill(
    "React.js",
    ["React", "Angular", "Vue"]
)
print(response.matched_skill)  # "React"
print(response.confidence)     # 0.95
```

#### `extract_skills(job_title, job_description, requirements=None)`

Extract skills from job description using LLM.

**Parameters:**
- `job_title` (str): Job title
- `job_description` (str): Full job description
- `requirements` (str, optional): Requirements section

**Returns:**
- `List[str]`: List of extracted skill names

**Example:**
```python
client = DeepSeekClient()
skills = client.extract_skills(
    "Senior Python Developer",
    "We need Python, Django, PostgreSQL..."
)
print(skills)  # ["Python", "Django", "PostgreSQL"]
```

### SkillNormalizer

#### `normalize(text)`

Apply full normalization pipeline to text.

**Parameters:**
- `text` (str): Raw skill string

**Returns:**
- `str`: Normalized skill string

**Example:**
```python
from easyhire_scout.skills.skill_normalizer import SkillNormalizer

normalized = SkillNormalizer.normalize("React.js")
print(normalized)  # "react"
```

## Confidence Scoring

| Confidence | Tier | Meaning | Auto-Accept | Needs Review |
|------------|------|---------|-------------|--------------|
| 1.0 | Exact | Exact match on canonical name | ✅ Yes | ❌ No |
| 0.95 | Exact | Exact match on known variant | ✅ Yes | ❌ No |
| 0.90 | Fuzzy | Fuzzy score >= 95 | ✅ Yes | ❌ No |
| 0.85 | Fuzzy | Fuzzy score >= 85 | ⚠️ Maybe | ✅ Yes |
| 0.70-0.84 | LLM | LLM match with medium confidence | ⚠️ Maybe | ✅ Yes |
| 0.50-0.69 | LLM | LLM match with low confidence | ❌ No | ✅ Yes |
| 0.0 | None | No match found | ❌ No | ✅ Yes |

**Thresholds:**
- Auto-accept: `confidence >= 0.85`
- Human review: `0.50 <= confidence < 0.85`
- Reject: `confidence < 0.50`

## Error Handling

### Typed Error Hierarchy

```python
SkillMatchError (base)
├── LLMAPIError (retryable if 5xx or 429)
├── LLMTimeoutError (retryable)
├── SkillNotFoundError (not retryable)
└── InvalidSkillInputError (not retryable)
```

### Graceful Degradation

- Tier 1 fails → Try Tier 2
- Tier 2 fails → Try Tier 3
- Tier 3 fails → Return no-match result
- Job still saved with raw skill text
- Background task retries unmatched skills later

### Retry Logic

```python
# Automatic retry with exponential backoff
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((LLMTimeoutError, LLMAPIError))
)
```

**Retry behavior:**
- Max 3 attempts
- Wait: 2s, 4s, 8s (exponential backoff)
- Only retry transient failures (5xx, timeout, 429)
- Never retry 4xx client errors

## Performance Metrics

### Target Performance

| Metric | Target | Actual (Expected) |
|--------|--------|-------------------|
| Tier 1 match rate | 80% | 75-85% |
| Tier 2 match rate | 15% | 10-20% |
| Tier 3 match rate | 5% | 3-8% |
| Tier 1 latency | <1ms | <1ms |
| Tier 2 latency | <10ms | 5-15ms |
| Tier 3 latency | <2s | 1-3s |
| Match accuracy | >95% | 92-97% |
| API cost per job | <$0.01 | $0.005-0.015 |

### Monitoring

```python
# Structured logging with metrics
logger.info("Skill matching completed", extra={
    "skill_count": 10,
    "duration_ms": 125.5,
    "tier_stats": {
        "exact": 7,
        "fuzzy": 2,
        "llm": 1,
        "none": 0
    }
})
```

## Testing

### Unit Tests

```bash
# Run normalizer tests
pytest easyhire_scout/skills/tests/test_normalizer.py

# Run matcher tests
pytest easyhire_scout/skills/tests/test_matcher.py

# Run LLM client tests (requires API key)
pytest easyhire_scout/skills/tests/test_llm_client.py
```

### Integration Tests

```bash
# End-to-end test with real database and API
pytest easyhire_scout/skills/tests/test_integration.py
```

## Troubleshooting

### Issue: "Missing required env var: DEEPSEEK_API_KEY"

**Solution:** Add your API key to `.env` file:
```bash
echo "DEEPSEEK_API_KEY=sk-your-key-here" >> .env
```

### Issue: LLM matching always fails

**Possible causes:**
1. Invalid API key
2. Rate limit exceeded
3. Network connectivity issues

**Solution:**
```bash
# Check API key is valid
curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  https://api.deepseek.com/v1/models

# Disable LLM temporarily
echo "ENABLE_LLM_MATCHING=false" >> .env
```

### Issue: Low match rate

**Possible causes:**
1. Skills not seeded in database
2. Skill names don't match canonical forms

**Solution:**
```bash
# Re-run seed script
python scripts/seed_skills.py

# Check skill count
python -c "from easyhire_scout.database import SessionLocal; \
from easyhire_scout.models import Skill; \
db = SessionLocal(); \
print(f'Skills in DB: {db.query(Skill).count()}')"
```

## Future Enhancements

### Phase 7 (Planned)

1. **LLM Response Caching**
   - Add `skill_llm_cache` table
   - Cache LLM responses for 30 days
   - Reduce API costs by 90%

2. **Auto-Learning Variants**
   - When LLM resolves a new variant, auto-create SkillVariant
   - Gradually improve Tier 1 match rate

3. **Confidence Calibration**
   - Track match accuracy over time
   - Adjust confidence thresholds dynamically

4. **Skill Clustering**
   - Group related skills (e.g., "React" + "Redux" + "React Router")
   - Suggest skill combinations

## Support

For issues or questions:
1. Check this documentation
2. Review error logs with structured logging
3. Test with `ENABLE_LLM_MATCHING=false` to isolate LLM issues
4. Verify database has seeded skills

## License

MIT License - See LICENSE file for details.