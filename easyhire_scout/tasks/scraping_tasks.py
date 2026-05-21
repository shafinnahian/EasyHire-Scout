from easyhire_scout.celery_app import celery_app
from easyhire_scout.services.scraping_service import ScrapingService
from easyhire_scout.database import db_session
import time
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="easyhire_scout.tasks.scraping_tasks.run_scrape")
def run_scrape(self, run_id: int, criteria: dict):
    """
    Background task to execute a scraping run.
    In Stage 1, this is a skeleton that simulates the process.
    """
    logger.info(f"Starting scrape run {run_id} with criteria: {criteria}")
    
    try:
        # Simulate work
        self.update_state(state='PROGRESS', meta={'progress': 10})
        time.sleep(2)
        
        self.update_state(state='PROGRESS', meta={'progress': 50})
        time.sleep(2)
        
        self.update_state(state='PROGRESS', meta={'progress': 90})
        time.sleep(1)
        
        # Update database status and create dummy data for testing
        with db_session() as db:
            from easyhire_scout.models import Company, Job, Location
            
            # 1. Resolve a dummy company
            company = db.query(Company).filter(Company.name == "EasyHire AI").first()
            if not company:
                company = Company(name="EasyHire AI", industry="Technology")
                db.add(company)
                db.flush()

            # 2. Resolve a dummy location
            location = db.query(Location).filter(Location.city == "Berlin").first()
            if not location:
                location = Location(city="Berlin", country="Germany", remote=True)
                db.add(location)
                db.flush()

            # 3. Create dummy jobs
            job_title = criteria.get("job_role", "Software Engineer")
            dummy_jobs = [
                Job(
                    title=f"Senior {job_title}",
                    description=f"We are looking for an expert in {job_title}. Remote position.",
                    company_id=company.id,
                    location_id=location.id,
                    scrape_run_id=run_id,
                    source_url=f"https://example.com/jobs/{run_id}/1",
                    salary_min=90000,
                    is_active=True
                ),
                Job(
                    title=f"Staff {job_title}",
                    description=f"Leadership role for a talented {job_title}.",
                    company_id=company.id,
                    location_id=location.id,
                    scrape_run_id=run_id,
                    source_url=f"https://example.com/jobs/{run_id}/2",
                    salary_min=120000,
                    is_active=True
                )
            ]
            db.add_all(dummy_jobs)

            ScrapingService.update_run_status(
                db, 
                run_id=run_id, 
                status="completed", 
                jobs_found=2, 
                jobs_saved=2
            )
        
        logger.info(f"Completed scrape run {run_id}")
        return {"run_id": run_id, "status": "completed", "jobs_found": 10}
        
    except Exception as e:
        logger.error(f"Scrape run {run_id} failed: {str(e)}")
        with db_session() as db:
            ScrapingService.update_run_status(db, run_id=run_id, status="failed")
        raise e
