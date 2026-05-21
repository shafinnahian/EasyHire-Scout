"""
EasyHire Scout - Stage 1 Database Models
PostgreSQL DDL - 3NF Normalized
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    TIMESTAMP,
    JSON,
    UniqueConstraint,
    Index,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ========================================
# CORE BUSINESS ENTITIES
# ========================================


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    normalized_name: Mapped[Optional[str]] = mapped_column(String(255))
    website: Mapped[Optional[str]] = mapped_column(String(500))
    careers_url: Mapped[Optional[str]] = mapped_column(String(500))
    headquarters_location_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("locations.id", ondelete="SET NULL")
    )
    industry: Mapped[Optional[str]] = mapped_column(String(100))
    company_size: Mapped[Optional[str]] = mapped_column(String(50))
    founded_year: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_companies_name_btree", "name"),
        Index("idx_companies_normalized_name", "normalized_name"),
        Index("idx_companies_headquarters_location", "headquarters_location_id"),
        Index(
            "idx_companies_name_fts",
            text("to_tsvector('english', name)"),
            postgresql_using="gin",
        ),
    )


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    region: Mapped[Optional[str]] = mapped_column(String(100))
    remote: Mapped[bool] = mapped_column(Boolean, default=False)
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 8))
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(11, 8))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("city", "country", "region"),
        Index("idx_locations_city", "city"),
        Index("idx_locations_country", "country"),
        Index("idx_locations_remote", "remote"),
    )


class JobCategory(Base):
    __tablename__ = "job_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )


# ========================================
# SCRAPING TRACKING
# ========================================


class ScrapeSite(Base):
    __tablename__ = "scrape_sites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    base_url: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )


class SearchCriteria(Base):
    """
    Represents a unique 'Search Intent' or 'Cohort' for the scraper.
    
    ARCHITECTURAL DECISION:
    1. Canonical Hashing Protocol: `cohort_hash` MUST be generated using a strict 
       canonicalization pipeline (lowercase, sort arrays, deterministic JSON string) 
       BEFORE hashing (SHA-256). This guarantees mathematical uniqueness and prevents
       duplicate scraping runs for identical intents (e.g. skills=["A", "B"] vs ["B", "A"]).
    
    2. JSONB Configuration: `parameters` deliberately violates strict 3NF. 
       This table is an IMMUTABLE INTENT LOG, not an analytical query target. 
       Storing skills/filters as JSONB keeps the POST /start API lightning fast 
       by avoiding synchronous string-to-entity database resolution.
    """
    __tablename__ = "search_criteria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scrape_site_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("scrape_sites.id", ondelete="CASCADE")
    )
    job_role: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    language_strict: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Storage for skills and additional_filters (years_min, job_type, etc.)
    # This ensures the cohort_hash captures the ENTIRE state of the search
    parameters: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    normalized_role: Mapped[Optional[str]] = mapped_column(String(255))
    normalized_location: Mapped[Optional[str]] = mapped_column(String(255))
    cohort_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_search_criteria_cohort", "cohort_hash"),
        Index("idx_search_criteria_site_role_loc", "scrape_site_id", "job_role", "location"),
    )


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scrape_site_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("scrape_sites.id", ondelete="SET NULL")
    )
    search_criteria_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("search_criteria.id", ondelete="SET NULL")
    )
    
    # Relationships
    scrape_site: Mapped[Optional["ScrapeSite"]] = relationship()
    search_criteria: Mapped[Optional["SearchCriteria"]] = relationship()

    started_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    status: Mapped[str] = mapped_column(String(50), default="running")
    jobs_found: Mapped[int] = mapped_column(Integer, default=0)
    jobs_saved: Mapped[int] = mapped_column(Integer, default=0)
    warnings: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_scrape_runs_site", "scrape_site_id"),
        Index("idx_scrape_runs_criteria", "search_criteria_id"),
        Index("idx_scrape_runs_status", "status"),
        Index("idx_scrape_runs_started", "started_at"),
    )


class ScrapeError(Base):
    __tablename__ = "scrape_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scrape_run_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("scrape_runs.id", ondelete="CASCADE")
    )
    error_url: Mapped[Optional[str]] = mapped_column(String(500))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_type: Mapped[Optional[str]] = mapped_column(String(50))
    occurred_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_scrape_errors_run", "scrape_run_id"),
        Index("idx_scrape_errors_type", "error_type"),
        Index("idx_scrape_errors_url", "error_url"),
    )


# ========================================
# CORE JOBS TABLE
# ========================================


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE")
    )
    location_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("locations.id", ondelete="SET NULL")
    )
    scrape_run_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("scrape_runs.id", ondelete="SET NULL")
    )
    search_criteria_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("search_criteria.id", ondelete="SET NULL")
    )
    source_site_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("scrape_sites.id", ondelete="SET NULL")
    )

    # Relationships
    company: Mapped[Optional["Company"]] = relationship()
    location: Mapped[Optional["Location"]] = relationship()
    scrape_run: Mapped[Optional["ScrapeRun"]] = relationship()
    search_criteria: Mapped[Optional["SearchCriteria"]] = relationship()
    source_site: Mapped[Optional["ScrapeSite"]] = relationship()
    skills: Mapped[List["Skill"]] = relationship(secondary="job_skills")
    languages: Mapped[List["JobLanguage"]] = relationship()
    categories: Mapped[List["JobCategory"]] = relationship(secondary="job_categories_link")

    # External identifiers
    external_id: Mapped[Optional[str]] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_title: Mapped[Optional[str]] = mapped_column(String(255))

    # Experience requirements
    years_min: Mapped[Optional[int]] = mapped_column(Integer)
    years_max: Mapped[Optional[int]] = mapped_column(Integer)
    years_overall: Mapped[bool] = mapped_column(Boolean, default=False)

    # Salary
    salary_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    salary_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    salary_currency: Mapped[str] = mapped_column(String(3), default="EUR")

    # Job metadata
    job_type: Mapped[Optional[str]] = mapped_column(String(50))
    employment_type: Mapped[Optional[str]] = mapped_column(String(50))

    # Content
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[Optional[str]] = mapped_column(Text)
    responsibilities: Mapped[Optional[str]] = mapped_column(Text)

    # Language requirements
    requires_german: Mapped[bool] = mapped_column(Boolean, default=False)

    # Dates
    posted_date: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True)
    )
    scraped_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )

    # Source
    source_url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_jobs_company", "company_id"),
        Index("idx_jobs_location", "location_id"),
        Index("idx_jobs_scrape_run", "scrape_run_id"),
        Index("idx_jobs_criteria", "search_criteria_id"),
        Index("idx_jobs_source_site", "source_site_id"),
        Index("idx_jobs_years", "years_min", "years_max"),
        Index("idx_jobs_last_seen", "last_seen_at"),
        Index(
            "idx_jobs_title",
            text("to_tsvector('english', title)"),
            postgresql_using="gin",
        ),
        Index("idx_jobs_posted", "posted_date"),
        Index("idx_jobs_source_url", "source_url"),
        Index("idx_jobs_requires_german", "requires_german"),
        Index("idx_jobs_job_type", "job_type"),
        Index("idx_jobs_is_active", "is_active"),
        Index("idx_jobs_external_id", "external_id"),
        Index(
            "idx_jobs_description_fts",
            text("to_tsvector('english', description || ' ' || COALESCE(requirements, ''))"),
            postgresql_using="gin",
        ),
    )


# ========================================
# LANGUAGE REQUIREMENTS (Normalized)
# ========================================


class JobLanguage(Base):
    __tablename__ = "job_languages"

    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True
    )
    language: Mapped[str] = mapped_column(String(50), nullable=False, primary_key=True)
    requirement_level: Mapped[str] = mapped_column(String(20), default="required")

    __table_args__ = (
        Index("idx_job_languages_job", "job_id"),
        Index("idx_job_languages_language", "language"),
        Index("idx_job_languages_level", "requirement_level"),
        Index("idx_job_languages_language_level", "language", "requirement_level"),
    )


# ========================================
# SKILLS SYSTEM
# ========================================


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    category: Mapped[Optional[str]] = mapped_column(String(50))
    typical_years_min: Mapped[Optional[int]] = mapped_column(Integer)
    typical_years_max: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_skills_category", "category"),
        Index("idx_skills_canonical_name_btree", "canonical_name"),
        Index(
            "idx_skills_name_fts",
            text("to_tsvector('english', canonical_name)"),
            postgresql_using="gin",
        ),
    )


class SkillVariant(Base):
    __tablename__ = "skill_variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.id", ondelete="CASCADE")
    )
    variant_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("skill_id", "variant_name"),
        Index("idx_skill_variants_name", "variant_name"),
        Index("idx_skill_variants_skill", "skill_id"),
    )


# ========================================
# JUNCTION TABLES (M:N RELATIONSHIPS)
# ========================================


class JobCategoryLink(Base):
    __tablename__ = "job_categories_link"

    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True
    )
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("job_categories.id", ondelete="CASCADE"), primary_key=True
    )


class JobSkill(Base):
    __tablename__ = "job_skills"

    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    weight: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("1.0"))

    __table_args__ = (
        Index("idx_job_skills_job", "job_id"),
        Index("idx_job_skills_skill", "skill_id"),
        Index("idx_job_skills_weight", "weight"),
    )
