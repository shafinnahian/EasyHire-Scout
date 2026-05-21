from typing import List, Optional, Tuple
from sqlalchemy import func, or_, and_, desc
from sqlalchemy.orm import Session, joinedload
from easyhire_scout.models import Job, Company, Location, ScrapeSite, ScrapeRun
from decimal import Decimal

class JobService:
    """
    Service for high-performance job retrieval and linguistic search.
    Implements Platform-Wide Linguistic Search (PostgreSQL FTS).
    """

    @staticmethod
    def list_jobs_with_ranking(
        db: Session,
        query: Optional[str] = None,
        min_salary: Optional[Decimal] = None,
        max_years: Optional[int] = None,
        is_remote: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Job], int]:
        """
        Retrieves jobs with FTS ranking and advanced filtering.
        Returns a tuple of (jobs, total_count).
        """
        # 1. Base query with optimized joins (Eager loading for WOW factor performance)
        base_query = db.query(Job).options(
            joinedload(Job.company),
            joinedload(Job.location),
            joinedload(Job.source_site)
        )

        filters = [Job.is_active == True]

        # 2. Linguistic Search (FTS Ranking)
        # Decision: Use websearch_to_tsquery for natural search syntax (e.g. "Python -java")
        relevance_score = None
        if query:
            # PostgreSQL FTS logic
            ts_query = func.websearch_to_tsquery('english', query)
            
            # Combine title and description for the search vector
            # This matches the Index defined in models.py (idx_jobs_description_fts)
            # but we use a simpler combined vector for flexibility here
            search_vector = func.to_tsvector('english', Job.title + ' ' + Job.description)
            
            filters.append(search_vector.op('@@')(ts_query))
            
            # Define relevance score for ordering
            relevance_score = func.ts_rank(search_vector, ts_query).label('relevance_score')
            base_query = base_query.add_columns(relevance_score)

        # 3. Structural Filters
        if min_salary:
            filters.append(Job.salary_min >= min_salary)
        if max_years is not None:
            filters.append(Job.years_min <= max_years)
        if is_remote is not None:
            base_query = base_query.join(Location)
            filters.append(Location.remote == is_remote)

        # Apply all filters
        base_query = base_query.filter(and_(*filters))

        # 4. Ordering
        # Priority: Relevance (if query exists) -> Posted Date -> Scraped Date
        if relevance_score is not None:
            base_query = base_query.order_by(desc('relevance_score'))
        else:
            base_query = base_query.order_by(desc(Job.posted_date), desc(Job.scraped_at))

        # 5. Pagination and Execution
        total = base_query.count()
        skip = (page - 1) * page_size
        
        # If we added columns (relevance_score), the result will be a list of tuples
        results = base_query.offset(skip).limit(page_size).all()
        
        # Normalize result to always return Job objects with attached score
        jobs = []
        for row in results:
            if isinstance(row, tuple):
                job_obj = row[0]
                # Attach relevance score dynamically for the schema to pick up
                job_obj.relevance_score = row[1]
                jobs.append(job_obj)
            else:
                job_obj = row
                job_obj.relevance_score = 0.0
                jobs.append(job_obj)

        return jobs, total

    @staticmethod
    def get_job_by_id(db: Session, job_id: int) -> Optional[Job]:
        """Retrieves a single job with all related metadata."""
        return db.query(Job).options(
            joinedload(Job.company),
            joinedload(Job.location),
            joinedload(Job.source_site),
            joinedload(Job.scrape_run)
        ).filter(Job.id == job_id).first()
