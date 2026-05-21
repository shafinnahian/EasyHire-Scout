from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

class CategoryInfo(BaseModel):
    """Information about a job category."""
    id: int
    name: str

    class Config:
        from_attributes = True    # To convert SQLAlchemy models to Pydantic models
    
class LanguageInfo(BaseModel):
    """Language requirement information"""
    language: str
    requirement_level: str  # "required", "preferred", "native", "fluent"
    
    class Config:
        from_attributes = True

class SkillInfo(BaseModel):
    """Information about a job skill."""
    id: int
    canonical_name: str
    category: Optional[str] = None
    weight: Decimal = Field(description="Skill weight 1 = required, 0.7 = nice to have")

    class Config:
        from_attributes = True

class LocationInfo(BaseModel):
    """Location information of the job responses."""
    id : int
    city : Optional[str] = None
    country : Optional[str] = None
    region : Optional[str] = None
    remote : bool
    latitude : Optional[Decimal] = None
    longitude : Optional[Decimal] = None

    class Config:
        from_attributes = True

class CompanyInfo(BaseModel):
    """Company information in job responses"""
    id: int
    name: str
    normalized_name: Optional[str] = None
    website: Optional[str] = None
    careers_url: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    founded_year: Optional[int] = None
    
    class Config:
        from_attributes = True

# Add these schemas after CompanyInfo:

class ScrapeSiteInfo(BaseModel):
    """Scraping source site information"""
    id: int
    name: str
    base_url: Optional[str] = None
    
    class Config:
        fromAttributes = True

class ScrapeRunInfo(BaseModel):
    """Scraping run information"""
    id: int
    scrape_site_id: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    jobs_found: int
    jobs_saved: int
    
    class Config:
        fromAttributes = True

class JobResponse(BaseModel):
    """Complete job response with all related data"""
    id: int
    title: str
    normalized_title: Optional[str] = None
    description: str
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    external_id: Optional[str] = None
    years_min: Optional[int] = None
    years_max: Optional[int] = None
    years_overall: bool = False
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    salary_currency: str = "EUR"
    job_type: Optional[str] = None
    employment_type: Optional[str] = None
    requires_german: bool = False
    posted_date: Optional[datetime] = None
    scraped_at: datetime
    source_url: str
    is_active: bool = True
    is_duplicate: bool = False
    created_at: datetime
    updated_at: datetime
    relevance_score: float = 0.0
    
    # Related entities
    company: Optional[CompanyInfo] = None
    location: Optional[LocationInfo] = None
    skills: list[SkillInfo] = []
    languages: list[LanguageInfo] = []
    categories: list[CategoryInfo] = []
    scrape_run: Optional[ScrapeRunInfo] = None
    source_site: Optional[ScrapeSiteInfo] = None
    
    class Config:
        fromAttributes = True