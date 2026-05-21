import os
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from easyhire_scout.database import SessionLocal
from easyhire_scout.models import ScrapeSite

def seed_sites():
    """
    Seeds the database with initial job sites.
    """
    db = SessionLocal()
    try:
        sites = [
            {"name": "LinkedIn", "base_url": "https://www.linkedin.com/jobs"},
            {"name": "Indeed", "base_url": "https://www.indeed.com"},
            {"name": "StepStone", "base_url": "https://www.stepstone.de"},
        ]
        
        print("--- Seeding Scrape Sites ---")
        for site_data in sites:
            exists = db.query(ScrapeSite).filter(ScrapeSite.name == site_data["name"]).first()
            if not exists:
                site = ScrapeSite(**site_data)
                db.add(site)
                print(f"[+] Added site: {site_data['name']}")
            else:
                print(f"[-] Site already exists: {site_data['name']}")
        
        db.commit()
        print("--- Seeding Complete ---")
    except Exception as e:
        print(f"[!] Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_sites()
