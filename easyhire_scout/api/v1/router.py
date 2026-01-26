from fastapi import APIRouter

# We will add the routes for the v1 API here
# Imported route modules will be added here after they are created, like jobs.py, companies.py, etc.

router = APIRouter(tags=["v1"])

# Future route modules (will be uncommented as we create them)
# api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
# api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
# api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
# api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
# api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
# api_router.include_router(scraping.router, prefix="/scraping", tags=["scraping"])


@router.get("/health")
async def health_check():
    return {"status": "healthy", "message": "EasyHire Scout API is running"}