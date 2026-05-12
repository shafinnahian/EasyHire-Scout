from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from easyhire_scout.database import get_db
from easyhire_scout.schemas.scraping import ScrapingStartRequest, ScrapingStartResponse
from easyhire_scout.tasks.scraping_tasks import run_scrape
from easyhire_scout.models import ScrapeRun, ScrapeSite, SearchCriteria

router = APIRouter(prefix="/scraping", tags=["scraping"])

@router.post("/start", response_model=ScrapingStartResponse, status_code=status.HTTP_201_CREATED)
def start_scraping_run(
    request: ScrapingStartRequest,
    db: Session = Depends(get_db)
):
    """
    Start a background scraping run with the provided search criteria.
    """
    # 1. Verify scrape site exists
    site = db.query(ScrapeSite).filter(ScrapeSite.id == request.scrape_site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail=f"Scrape site with ID {request.scrape_site_id} not found")

    # 2. [TODO] Implement Canonical Hashing to resolve SearchCriteria cohort
    # For Stage 1 skeleton, we'll just create a placeholder or find existing
    # [Placeholder logic]
    
    # 3. Create ScrapeRun record
    new_run = ScrapeRun(
        scrape_site_id=site.id,
        status="running",
        started_at=datetime.utcnow(),
        # search_criteria_id would be resolved here
        jobs_found=0,
        jobs_saved=0
    )
    db.add(new_run)
    db.commit()
    db.refresh(new_run)

    # 4. Trigger background task
    # Passing criteria as dict for now
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
