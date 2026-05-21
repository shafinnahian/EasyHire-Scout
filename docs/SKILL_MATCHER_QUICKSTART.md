# Skill Matcher Service - Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
# Install package with new dependencies
pip install .
```

### 2. Configure API Key

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your DeepSeek API key
# Get your key from: https://platform.deepseek.com/api_keys
nano .env
```

Add this line to `.env`:
```env
DEEPSEEK_API_KEY=sk-your-actual-key-here
```

### 3. Seed Skills Database

```bash
# Populate database with 60+ core tech skills
python scripts/seed_skills.py
```

Expected output:
```
============================================================
SEEDING SKILLS
============================================================
[+] Created skill: Python (Programming Language)
    [+] Added variant: py
    [+] Added variant: python3
[+] Created skill: JavaScript (Programming Language)
    [+] Added variant: js
    [+] Added variant: ecmascript
...
============================================================
SEEDING COMPLETE
  Skills created: 60
  Skills skipped: 0
  Variants created: 150+
  Total skills in DB: 60
============================================================
```

### 4. Test the Service

```python
# test_skill_matcher.py
from easyhire_scout.database import SessionLocal
from easyhire_scout.skills import SkillMatcherService

db = SessionLocal()

# Test matching
results = SkillMatcherService.match_skills(
    db=db,
    raw_skills=["Python", "React.js", "ML", "k8s"],
    use_llm=True
)

for result in results:
    print(f"✓ {result.raw_input} → {result.skill_name} "
          f"(confidence: {result.confidence:.2f}, tier: {result.tier_used})")

db.close()
```

Expected output:
```
✓ Python → Python (confidence: 1.00, tier: exact)
✓ React.js → React (confidence: 0.95, tier: exact)
✓ ML → Machine Learning (confidence: 0.95, tier: exact)
✓ k8s → Kubernetes (confidence: 0.95, tier: exact)
```

## 📊 Understanding Results

### Match Result Fields

```python
MatchResult(
    raw_input="React.js",           # Original input
    skill_id=15,                     # Database ID
    skill_name="React",              # Canonical name
    confidence=0.95,                 # Match confidence (0.0-1.0)
    tier_used="exact",               # Matching tier used
    needs_review=False,              # Whether human review needed
    reasoning="Exact match on variant 'reactjs'"
)
```

### Confidence Levels

| Confidence | Meaning | Action |
|------------|---------|--------|
| 1.0 | Perfect match | ✅ Auto-accept |
| 0.95 | Known variant | ✅ Auto-accept |
| 0.90 | Strong fuzzy match | ✅ Auto-accept |
| 0.85 | Good fuzzy match | ⚠️ Review recommended |
| 0.70-0.84 | LLM match | ⚠️ Review recommended |
| < 0.70 | Weak/no match | ❌ Reject or manual review |

### Matching Tiers

| Tier | Speed | Cost | When Used |
|------|-------|------|-----------|
| `exact` | <1ms | Free | Normalized string matches canonical name or variant |
| `fuzzy` | <10ms | Free | RapidFuzz similarity >= 85% |
| `llm` | 1-3s | ~$0.001 | Semantic matching via DeepSeek API |
| `none` | N/A | Free | No match found in any tier |

## 🔧 Common Use Cases

### Use Case 1: Match Skills from Job Scraper

```python
from easyhire_scout.skills import SkillMatcherService

# Skills extracted from job posting
raw_skills = [
    "Python", "Django", "REST APIs", "PostgreSQL",
    "Docker", "AWS", "CI/CD", "Git"
]

results = SkillMatcherService.match_skills(db, raw_skills)

# Filter high-confidence matches
matched_skills = [
    r.skill_id for r in results 
    if r.skill_id and r.confidence >= 0.85
]

print(f"Matched {len(matched_skills)} skills with high confidence")
```

### Use Case 2: Background Processing (Celery)

```python
from easyhire_scout.tasks.skill_processing_tasks import process_skill_batch

# Queue batch processing (non-blocking)
task = process_skill_batch.delay(
    raw_skills=["Python", "React", "Docker"],
    use_llm=True
)

# Get task ID for tracking
print(f"Task queued: {task.id}")

# Later: check result
result = task.get(timeout=60)
print(f"Processed: {result['stats']['total_processed']}")
print(f"Matched: {result['stats']['matched']}")
```

### Use Case 3: Extract Skills from Job Description

```python
from easyhire_scout.tasks.skill_processing_tasks import extract_and_match_skills

# Extract and match in one step
task = extract_and_match_skills.delay(
    job_id=123,
    job_title="Senior Python Developer",
    job_description="""
    We're looking for a Senior Python Developer with experience in:
    - Python and Django
    - PostgreSQL and Redis
    - Docker and Kubernetes
    - AWS cloud services
    """,
    requirements="5+ years Python, 3+ years Django"
)

result = task.get()
print(f"Extracted: {result['extracted_skills']}")
print(f"Matched: {len(result['matched_skills'])} skills")
```

## 🎯 Best Practices

### 1. Batch Processing

✅ **DO**: Process skills in batches
```python
# Good: Process 10 skills in one call
results = SkillMatcherService.match_skills(db, skill_list)
```

❌ **DON'T**: Process one skill at a time
```python
# Bad: 10 separate calls
for skill in skill_list:
    result = SkillMatcherService.match_skills(db, [skill])
```

### 2. LLM Usage

✅ **DO**: Use LLM for unmatched skills only
```python
# First pass without LLM (fast, free)
results = SkillMatcherService.match_skills(db, skills, use_llm=False)

# Second pass with LLM for unmatched only
unmatched = [r.raw_input for r in results if not r.skill_id]
if unmatched:
    llm_results = SkillMatcherService.match_skills(db, unmatched, use_llm=True)
```

❌ **DON'T**: Always use LLM
```python
# Bad: Wastes API credits on skills that match in Tier 1/2
results = SkillMatcherService.match_skills(db, skills, use_llm=True)
```

### 3. Error Handling

✅ **DO**: Handle graceful degradation
```python
try:
    results = SkillMatcherService.match_skills(db, skills)
except Exception as e:
    logger.error(f"Skill matching failed: {e}")
    # Job still saved with raw skill text
    # Background task will retry later
```

### 4. Confidence Thresholds

✅ **DO**: Filter by confidence
```python
# Only use high-confidence matches
high_confidence = [r for r in results if r.confidence >= 0.85]

# Flag low-confidence for review
needs_review = [r for r in results if r.needs_review]
```

## 🐛 Troubleshooting

### Problem: "Missing required env var: DEEPSEEK_API_KEY"

**Solution:**
```bash
# Check if .env file exists
ls -la .env

# Add API key
echo "DEEPSEEK_API_KEY=sk-your-key-here" >> .env
```

### Problem: No skills matched (all tier: "none")

**Solution:**
```bash
# Check if skills are seeded
python -c "from easyhire_scout.database import SessionLocal; \
from easyhire_scout.models import Skill; \
db = SessionLocal(); \
print(f'Skills in DB: {db.query(Skill).count()}')"

# If 0, run seed script
python scripts/seed_skills.py
```

### Problem: LLM matching fails

**Solution:**
```bash
# Test API key
curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  https://api.deepseek.com/v1/models

# Temporarily disable LLM
echo "ENABLE_LLM_MATCHING=false" >> .env
```

### Problem: Slow performance

**Possible causes:**
1. Using LLM for every skill (expensive)
2. Not batching requests
3. Database not indexed

**Solution:**
```python
# Use LLM sparingly
results = SkillMatcherService.match_skills(db, skills, use_llm=False)

# Batch process
process_skill_batch.delay(skills)  # Async

# Check database indexes
# Run: python scripts/check_indexes.py
```

## 📈 Monitoring

### Check Match Statistics

```python
from easyhire_scout.skills import SkillMatcherService

results = SkillMatcherService.match_skills(db, skills)

# Calculate statistics
stats = {
    "total": len(results),
    "matched": sum(1 for r in results if r.skill_id),
    "exact": sum(1 for r in results if r.tier_used == "exact"),
    "fuzzy": sum(1 for r in results if r.tier_used == "fuzzy"),
    "llm": sum(1 for r in results if r.tier_used == "llm"),
    "none": sum(1 for r in results if r.tier_used == "none"),
}

print(f"Match rate: {stats['matched']/stats['total']*100:.1f}%")
print(f"Tier distribution: {stats}")
```

### View Logs

```bash
# Structured JSON logs
tail -f logs/easyhire_scout.log | jq .

# Filter skill matching operations
tail -f logs/easyhire_scout.log | jq 'select(.operation == "skill_match")'
```

## 🚀 Next Steps

1. **Integrate with Job Scraper**
   - Call `SkillMatcherService.match_skills()` after scraping
   - Store matched skill IDs in `job_skills` table

2. **Add Skill-Based Search**
   - Filter jobs by skill IDs
   - Use confidence scores for ranking

3. **Implement Review Queue**
   - Show jobs with `needs_review=True`
   - Allow manual skill assignment

4. **Monitor API Costs**
   - Track LLM API usage
   - Optimize by caching responses

## 📚 Full Documentation

For complete API reference and advanced usage:
- [Full Implementation Docs](./SKILL_MATCHER_IMPLEMENTATION.md)
- [Architecture Plan](../README.md)

## 💡 Tips

- Start with `use_llm=False` to test Tier 1 & 2
- Seed more skills as you discover new ones
- Monitor `needs_review` flag for quality control
- Use background tasks for large batches
- Cache LLM responses to reduce costs

## ✅ Checklist

- [ ] Dependencies installed (`pip install .`)
- [ ] API key configured in `.env`
- [ ] Skills seeded (`python scripts/seed_skills.py`)
- [ ] Test script runs successfully
- [ ] Celery worker running (for background tasks)
- [ ] Logs configured and monitored

---

**Ready to use!** 🎉

For questions or issues, see [Troubleshooting](#-troubleshooting) or check the full documentation.