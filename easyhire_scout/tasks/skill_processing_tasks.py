"""
Celery tasks for batch skill processing.

Implements async batch processing to minimize LLM API costs:
- Processes pending skills in batches
- Caches LLM responses
- Handles failures gracefully

Follows fullstack-dev Section 8: Background Jobs & Async.
"""

import logging
from typing import List
from celery import Task

from easyhire_scout.celery_app import celery_app
from easyhire_scout.database import db_session
from easyhire_scout.skills.skill_matcher import SkillMatcherService
from easyhire_scout.skills.schemas import MatchResult

logger = logging.getLogger(__name__)


class SkillProcessingTask(Task):
    """Base task with error handling for skill processing."""
    
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}  # Retry after 1 min
    retry_backoff = True
    retry_backoff_max = 600  # Max 10 minutes
    retry_jitter = True


@celery_app.task(
    bind=True,
    base=SkillProcessingTask,
    name="easyhire_scout.tasks.skill_processing_tasks.process_skill_batch"
)
def process_skill_batch(self, raw_skills: List[str], use_llm: bool = True) -> dict:
    """
    Process a batch of raw skills through the matching pipeline.
    
    This task is idempotent - running it multiple times with the same
    input produces the same result.
    
    Args:
        raw_skills: List of raw skill strings to process
        use_llm: Whether to use LLM for Tier 3 matching
        
    Returns:
        dict with processing results and statistics
        
    Example:
        >>> from easyhire_scout.tasks.skill_processing_tasks import process_skill_batch
        >>> result = process_skill_batch.delay(["Python", "React.js", "ML"])
        >>> print(result.get())  # Wait for completion
    """
    logger.info(f"Starting skill batch processing", extra={
        "skill_count": len(raw_skills),
        "use_llm": use_llm,
        "task_id": self.request.id
    })
    
    try:
        with db_session() as db:
            # Process skills through matching pipeline
            results = SkillMatcherService.match_skills(
                db=db,
                raw_skills=raw_skills,
                use_llm=use_llm
            )
            
            # Calculate statistics
            stats = {
                "total_processed": len(results),
                "matched": sum(1 for r in results if r.skill_id is not None),
                "unmatched": sum(1 for r in results if r.skill_id is None),
                "needs_review": sum(1 for r in results if r.needs_review),
                "tier_stats": {
                    "exact": sum(1 for r in results if r.tier_used == "exact"),
                    "fuzzy": sum(1 for r in results if r.tier_used == "fuzzy"),
                    "llm": sum(1 for r in results if r.tier_used == "llm"),
                    "none": sum(1 for r in results if r.tier_used == "none"),
                }
            }
            
            logger.info(f"Skill batch processing completed", extra={
                "task_id": self.request.id,
                **stats
            })
            
            return {
                "status": "completed",
                "task_id": self.request.id,
                "results": [r.model_dump() for r in results],
                "stats": stats
            }
            
    except Exception as e:
        logger.error(f"Skill batch processing failed: {e}", extra={
            "task_id": self.request.id,
            "skill_count": len(raw_skills),
            "error": str(e)
        })
        raise


@celery_app.task(
    bind=True,
    base=SkillProcessingTask,
    name="easyhire_scout.tasks.skill_processing_tasks.extract_and_match_skills"
)
def extract_and_match_skills(
    self,
    job_id: int,
    job_title: str,
    job_description: str,
    requirements: str | None = None
) -> dict:
    """
    Extract skills from job description and match them to canonical skills.
    
    Two-step process:
    1. Use LLM to extract skills from job text
    2. Match extracted skills to canonical skills in database
    
    Args:
        job_id: Job ID for tracking
        job_title: Job title
        job_description: Full job description
        requirements: Optional requirements section
        
    Returns:
        dict with extracted and matched skills
        
    Example:
        >>> result = extract_and_match_skills.delay(
        ...     job_id=123,
        ...     job_title="Senior Python Developer",
        ...     job_description="We need Python, Django, PostgreSQL..."
        ... )
    """
    logger.info(f"Starting skill extraction for job {job_id}", extra={
        "job_id": job_id,
        "job_title": job_title,
        "task_id": self.request.id
    })
    
    try:
        from easyhire_scout.skills.llm_client import DeepSeekClient
        
        # Step 1: Extract skills using LLM
        client = DeepSeekClient()
        extracted_skills = client.extract_skills(
            job_title=job_title,
            job_description=job_description,
            requirements=requirements
        )
        
        if not extracted_skills:
            logger.warning(f"No skills extracted for job {job_id}")
            return {
                "status": "completed",
                "job_id": job_id,
                "extracted_skills": [],
                "matched_skills": [],
                "stats": {"extracted": 0, "matched": 0}
            }
        
        # Step 2: Match extracted skills to canonical skills
        with db_session() as db:
            match_results = SkillMatcherService.match_skills(
                db=db,
                raw_skills=extracted_skills,
                use_llm=False  # Already used LLM for extraction
            )
            
            matched_skills = [
                {
                    "raw": r.raw_input,
                    "skill_id": r.skill_id,
                    "skill_name": r.skill_name,
                    "confidence": r.confidence
                }
                for r in match_results
                if r.skill_id is not None
            ]
            
            logger.info(f"Skill extraction completed for job {job_id}", extra={
                "job_id": job_id,
                "extracted_count": len(extracted_skills),
                "matched_count": len(matched_skills),
                "task_id": self.request.id
            })
            
            return {
                "status": "completed",
                "job_id": job_id,
                "task_id": self.request.id,
                "extracted_skills": extracted_skills,
                "matched_skills": matched_skills,
                "stats": {
                    "extracted": len(extracted_skills),
                    "matched": len(matched_skills),
                    "match_rate": len(matched_skills) / len(extracted_skills) if extracted_skills else 0
                }
            }
            
    except Exception as e:
        logger.error(f"Skill extraction failed for job {job_id}: {e}", extra={
            "job_id": job_id,
            "task_id": self.request.id,
            "error": str(e)
        })
        raise


@celery_app.task(name="easyhire_scout.tasks.skill_processing_tasks.cleanup_old_cache")
def cleanup_old_cache(days: int = 30) -> dict:
    """
    Clean up old LLM response cache entries.
    
    Should be run periodically (e.g., daily) to prevent cache bloat.
    
    Args:
        days: Delete cache entries older than this many days
        
    Returns:
        dict with cleanup statistics
    """
    logger.info(f"Starting cache cleanup (older than {days} days)")
    
    # TODO: Implement cache table and cleanup logic
    # For now, this is a placeholder
    
    logger.info("Cache cleanup completed")
    
    return {
        "status": "completed",
        "days": days,
        "deleted_count": 0  # Placeholder
    }

# Made with Bob
