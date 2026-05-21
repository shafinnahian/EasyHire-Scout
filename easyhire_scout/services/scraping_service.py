from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from easyhire_scout.models import ScrapeRun, SearchCriteria
from easyhire_scout.services.hashing_service import HashingService

class ScrapingService:
    """
    Service for managing scraping runs and cohort resolution.
    Follows industrial best practices for decoupling logic from API/Tasks.
    """

    @staticmethod
    def resolve_cohort(db: Session, site_id: int, request_data: Dict[str, Any]) -> SearchCriteria:
        """
        Implements the 'Get or Create' logic for a SearchCohort.
        1. Generates the canonical cohort_hash.
        2. Retrieves existing criteria or creates a new one.
        """
        # Extract intent fields for hashing
        intent_data = {
            "site_id": site_id,
            "job_role": request_data.get("job_role"),
            "location": request_data.get("location"),
            "language": request_data.get("language"),
            "language_strict": request_data.get("language_strict", True),
            "additional_filters": request_data.get("additional_filters", {})
        }
        
        cohort_hash = HashingService.generate_cohort_hash(intent_data)
        
        # Check if criteria already exists
        criteria = db.query(SearchCriteria).filter(SearchCriteria.cohort_hash == cohort_hash).first()
        
        if not criteria:
            criteria = SearchCriteria(
                scrape_site_id=site_id,
                job_role=request_data.get("job_role"),
                location=request_data.get("location"),
                language=request_data.get("language"),
                language_strict=request_data.get("language_strict", True),
                parameters=request_data.get("additional_filters"),
                cohort_hash=cohort_hash
            )
            db.add(criteria)
            db.flush()  # Get the ID without committing the whole transaction yet
            
        return criteria

    @classmethod
    def initialize_run(cls, db: Session, site_id: int, request_data: Dict[str, Any]) -> ScrapeRun:
        """
        Orchestrates the start of a scraping run.
        1. Resolves the cohort (SearchCriteria).
        2. Creates the ScrapeRun record.
        """
        criteria = cls.resolve_cohort(db, site_id, request_data)
        
        new_run = ScrapeRun(
            scrape_site_id=site_id,
            search_criteria_id=criteria.id,
            status="running",
            started_at=datetime.utcnow()
        )
        db.add(new_run)
        db.commit()
        db.refresh(new_run)
        
        return new_run

    @staticmethod
    def update_run_status(db: Session, run_id: int, status: str, jobs_found: int = 0, jobs_saved: int = 0):
        """
        Updates the state of a run. To be called by Celery workers.
        """
        run = db.query(ScrapeRun).filter(ScrapeRun.id == run_id).first()
        if run:
            run.status = status
            run.jobs_found = jobs_found
            run.jobs_saved = jobs_saved
            if status in ["completed", "failed"]:
                run.completed_at = datetime.utcnow()
            db.commit()
