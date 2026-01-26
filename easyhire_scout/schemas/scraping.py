from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from easyhire_scout.schemas.job import ScrapeSiteInfo

class AdditionalSearchFilters(BaseModel):
    """Additional search criteria for scraping"""
    years_min: Optional[int] = None
    years_max: Optional[int] = None
    job_type: Optional[str] = None  # e.g., "full_time", "part_time", "contract", "working student", "internship"
    remote: Optional[bool] = None
    
    class Config:
        from_attributes = True

class ScrapingStartRequest(BaseModel):
    """Request schema for starting a scraping run"""
    scrape_site_id: int = Field(description="Which job site to scrape")
    job_role: str = Field(description="The job role/title to search for")
    location: str = Field(description="Location to search in")
    language: str = Field(description="Language requirement")
    language_strict: bool = Field(description="If true, only return jobs strictly in the specified language")
    additional_filters: Optional[AdditionalSearchFilters] = None

class SearchCriteria(BaseModel):
    """Search criteria used for a scraping run"""
    job_role: str
    location: str
    language: str
    language_strict: bool
    additional_filters: Optional[AdditionalSearchFilters] = None

class ScrapingStartResponse(BaseModel):
    """Response schema for starting a scraping run"""
    run_id: int
    status: str = Field(description="Running, Completed, Failed, Cancelled")
    scrape_site: ScrapeSiteInfo
    search_criteria: SearchCriteria
    started_at: datetime
    message: str

class ScrapeRunResponse(BaseModel):
    """Response schema for a scraping run"""
    id: int
    scrape_site_id: Optional[int] = None
    scrape_site: Optional[ScrapeSiteInfo] = None
    search_criteria: Optional[SearchCriteria] = None  # Stored as JSONB in database [TODO: Define search criteria schema]
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = Field(description="Running, Completed, Failed, Cancelled")
    jobs_found: int
    jobs_saved: int
    warnings: Optional[list[str]] = None  # Transformed from JSONB dict [TODO: Define warning schema]
    created_at: datetime
    
    class Config:
        from_attributes = True