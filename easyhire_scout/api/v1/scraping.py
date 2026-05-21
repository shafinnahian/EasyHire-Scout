from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from easyhire_scout.database import get_db
from easyhire_scout.schemas.scraping import ScrapingStartRequest, ScrapingStartResponse, ScrapingStatusResponse
from easyhire_scout.services.scraping_service import ScrapingService
from easyhire_scout.tasks.scraping_tasks import run_scrape
from easyhire_scout.models import ScrapeSite

router = APIRouter(prefix="/scraping", tags=["scraping"])

@router.post("/start", response_model=ScrapingStartResponse, status_code=status.HTTP_201_CREATED)
def start_scraping_run(
    request: ScrapingStartRequest,
    db: Session = Depends(get_db)
):
    """
    Start a background scraping run with the provided search criteria.
    Uses the Canonical Hashing Protocol to resolve search cohorts.
    """
    # 1. Verify scrape site exists
    site = db.query(ScrapeSite).filter(ScrapeSite.id == request.scrape_site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Scrape site with ID {request.scrape_site_id} not found"
        )

    # 2. Initialize run via Service (Handles hashing, SearchCriteria resolution, and ScrapeRun creation)
    new_run = ScrapingService.initialize_run(db, site.id, request.model_dump())

    # 3. Trigger background task
    run_scrape.delay(new_run.id, request.model_dump())

    return ScrapingStartResponse(
        run_id=new_run.id,
        status=new_run.status,
        scrape_site={
            "id": site.id,
            "name": site.name,
            "base_url": site.base_url
        },
        search_criteria=request.model_dump(),
        started_at=new_run.started_at,
        message="Scraping run started successfully"
    )

@router.get("/status/{run_id}", response_model=ScrapingStatusResponse)
def get_scraping_status(
    run_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the current status and results summary of a scraping run.
    """
    from easyhire_scout.models import ScrapeRun, ScrapeSite, SearchCriteria
    
    run = db.query(ScrapeRun).options(
        joinedload(ScrapeRun.search_criteria),
        joinedload(ScrapeRun.scrape_site)
    ).filter(ScrapeRun.id == run_id).first()
    
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scraping run with ID {run_id} not found"
        )
    
    # Map to schema
    return ScrapingStatusResponse(
        run_id=run.id,
        status=run.status,
        jobs_found=run.jobs_found,
        jobs_saved=run.jobs_saved,
        started_at=run.started_at,
        completed_at=run.completed_at,
        scrape_site_name=run.scrape_site.name if run.scrape_site else "Unknown",
        search_criteria={
            "job_role": run.search_criteria.job_role,
            "location": run.search_criteria.location,
            "language": run.search_criteria.language,
            "language_strict": run.search_criteria.language_strict,
            "additional_filters": run.search_criteria.parameters
        }
    )
