from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal

from easyhire_scout.database import get_db
from easyhire_scout.schemas.job import JobResponse
from easyhire_scout.schemas.common_pagination_structure import PaginatedResponse
from easyhire_scout.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.get("/", response_model=PaginatedResponse[JobResponse])
def list_jobs(
    query: Optional[str] = Query(None, description="Linguistic search (e.g. 'Python FastAPI')"),
    min_salary: Optional[Decimal] = Query(None, description="Minimum annual salary"),
    max_years: Optional[int] = Query(None, description="Maximum years of experience"),
    is_remote: Optional[bool] = Query(None, description="Filter by remote status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all active jobs with relevance ranking and filters.
    Utilizes PostgreSQL Full-Text Search for the 'query' parameter.
    """
    jobs, total = JobService.list_jobs_with_ranking(
        db,
        query=query,
        min_salary=min_salary,
        max_years=max_years,
        is_remote=is_remote,
        page=page,
        page_size=page_size
    )
    
    return PaginatedResponse.create(
        items=jobs,
        total=total,
        page=page,
        pageSize=page_size
    )

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information for a specific job.
    """
    job = JobService.get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )
    return job
