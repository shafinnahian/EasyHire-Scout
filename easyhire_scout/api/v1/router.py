from fastapi import APIRouter

# We will add the routes for the v1 API here
# Imported route modules will be added here after they are created, like jobs.py, companies.py, etc.

from easyhire_scout.api.v1 import scraping, jobs

router = APIRouter()

# Future route modules (will be uncommented as we create them)
router.include_router(jobs.router)
# router.include_router(companies.router, prefix="/companies", tags=["companies"])
# router.include_router(locations.router, prefix="/locations", tags=["locations"])
# router.include_router(skills.router, prefix="/skills", tags=["skills"])
# router.include_router(categories.router, prefix="/categories", tags=["categories"])
router.include_router(scraping.router)


@router.get("/health")
async def health_check():
    return {"status": "healthy", "message": "EasyHire Scout API is running"}