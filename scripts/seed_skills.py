"""
Seed script for populating canonical skills and variants.

Seeds 100+ core tech skills across categories:
- Programming Languages
- Frameworks & Libraries
- Databases
- Cloud & DevOps
- Tools & Platforms

Run this after database initialization to enable skill matching.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from easyhire_scout.database import SessionLocal
from easyhire_scout.models import Skill, SkillVariant

# Comprehensive skill data with variants
SKILLS_DATA = [
    # Programming Languages
    {
        "canonical_name": "Python",
        "category": "Programming Language",
        "variants": ["py", "python3", "python2"],
        "typical_years_min": 0,
        "typical_years_max": 15
    },
    {
        "canonical_name": "JavaScript",
        "category": "Programming Language",
        "variants": ["js", "ecmascript", "es6", "es2015", "es2020", "node", "nodejs"],
        "typical_years_min": 0,
        "typical_years_max": 12
    },
    {
        "canonical_name": "TypeScript",
        "category": "Programming Language",
        "variants": ["ts"],
        "typical_years_min": 0,
        "typical_years_max": 8
    },
    {
        "canonical_name": "Java",
        "category": "Programming Language",
        "variants": ["jdk", "jre"],
        "typical_years_min": 0,
        "typical_years_max": 20
    },
    {
        "canonical_name": "C++",
        "category": "Programming Language",
        "variants": ["cpp", "cplusplus", "c plus plus"],
        "typical_years_min": 0,
        "typical_years_max": 20
    },
    {
        "canonical_name": "C#",
        "category": "Programming Language",
        "variants": ["csharp", "c sharp", "cs", "dotnet"],
        "typical_years_min": 0,
        "typical_years_max": 15
    },
    {
        "canonical_name": "Go",
        "category": "Programming Language",
        "variants": ["golang"],
        "typical_years_min": 0,
        "typical_years_max": 10
    },
    {
        "canonical_name": "Rust",
        "category": "Programming Language",
        "variants": [],
        "typical_years_min": 0,
        "typical_years_max": 8
    },
    {
        "canonical_name": "Ruby",
        "category": "Programming Language",
        "variants": ["rb"],
        "typical_years_min": 0,
        "typical_years_max": 15
    },
    {
        "canonical_name": "PHP",
        "category": "Programming Language",
        "variants": [],
        "typical_years_min": 0,
        "typical_years_max": 20
    },
    {
        "canonical_name": "Swift",
        "category": "Programming Language",
        "variants": [],
        "typical_years_min": 0,
        "typical_years_max": 8
    },
    {
        "canonical_name": "Kotlin",
        "category": "Programming Language",
        "variants": [],
        "typical_years_min": 0,
        "typical_years_max": 8
    },
    
    # Frontend Frameworks
    {
        "canonical_name": "React",
        "category": "Frontend Framework",
        "variants": ["reactjs", "react.js", "react js"],
        "typical_years_min": 0,
        "typical_years_max": 8
    },
    {
        "canonical_name": "Vue",
        "category": "Frontend Framework",
        "variants": ["vuejs", "vue.js", "vue js"],
        "typical_years_min": 0,
        "typical_years_max": 7
    },
    {
        "canonical_name": "Angular",
        "category": "Frontend Framework",
        "variants": ["angularjs", "angular.js"],
        "typical_years_min": 0,
        "typical_years_max": 10
    },
    {
        "canonical_name": "Next.js",
        "category": "Frontend Framework",
        "variants": ["nextjs", "next"],
        "typical_years_min": 0,
        "typical_years_max": 5
    },
    {
        "canonical_name": "Svelte",
        "category": "Frontend Framework",
        "variants": ["sveltejs"],
        "typical_years_min": 0,
        "typical_years_max": 4
    },
    
    # Backend Frameworks
    {
        "canonical_name": "Django",
        "category": "Backend Framework",
        "variants": [],
        "typical_years_min": 0,
        "typical_years_max": 12
    },
    {
        "canonical_name": "FastAPI",
        "category": "Backend Framework",
        "variants": ["fast api"],
        "typical_years_min": 0,
        "typical_years_max": 4
    },
    {
        "canonical_name": "Flask",
        "category": "Backend Framework",
        "variants": [],
        "typical_years_min": 0,
        "typical_years_max": 10
    },
    {
        "canonical_name": "Express",
        "category": "Backend Framework",
        "variants": ["expressjs", "express.js"],
        "typical_years_min": 0,
        "typical_years_max": 10
    },
    {
        "canonical_name": "Spring Boot",
        "category": "Backend Framework",
        "variants": ["spring", "springboot"],
        "typical_years_min": 0,
        "typical_years_max": 15
    },
    {
        "canonical_name": "Ruby on Rails",
        "category": "Backend Framework",
        "variants": ["rails", "ror"],
        "typical_years_min": 0,
        "typical_years_max": 15
    },
    {
        "canonical_name": "Laravel",
        "category": "Backend Framework",
        "variants": [],
        "typical_years_min": 0,
        "typical_years_max": 10
    },
    {
        "canonical_name": "ASP.NET",
        "category": "Backend Framework",
        "variants": ["asp.net core", "aspnet"],
        "typical_years_min": 0,
        "typical_years_max": 15
    },
    
    # Databases
    {
        "canonical_name": "PostgreSQL",
        "category": "Database",
        "variants": ["postgres", "pg", "psql"],
        "typical_years_min": 0,
        "typical_years_max": 20
    },
    {
        "canonical_name": "MySQL",
        "category": "Database",
        "variants": ["my sql"],
        "typical_years_min": 0,
        "typical_years_max": 20
    },
    {
        "canonical_name": "MongoDB",
        "category": "Database",
        "variants": ["mongo"],
        "typical_years_min": 0,
        "typical_years_max": 12
    },
    {
        "canonical_name": "Redis",
        "category": "Database",
        "variants": [],
        "typical_years_min": 0,
        "typical_years_max": 12
    },
    {
        "canonical_name": "Elasticsearch",
        "category": "Database",
        "variants": ["elastic search", "elastic"],
        "typical_years_min": 0,
        "typical_years_max": 10
    },
    {
        "canonical_name": "SQLite",
        "category": "Database",
        "variants": ["sqlite3"],
        "typical_years_min": 0,
        "typical_years_max": 15
    },
    {
        "canonical_name": "Microsoft SQL Server",
        "category": "Database",
        "variants": ["mssql", "sql server", "sqlserver"],
        "typical_years_min": 0,
        "typical_years_max": 20
    },
    {
        "canonical_name": "Oracle Database",
        "category": "Database",
        "variants": ["oracle", "oracle db"],
        "typical_years_min": 0,
        "typical_years_max": 25
    },
    
    # Cloud Platforms
    {
        "canonical_name": "Amazon Web Services",
        "category": "Cloud Platform",
        "variants": ["aws", "amazon aws"],
        "typical_years_min": 0,
        "typical_years_max": 15
    },
    {
        "canonical_name": "Google Cloud Platform",
        "category": "Cloud Platform",
        "variants": ["gcp", "google cloud"],
        "typical_years_min": 0,
        "typical_years_max": 12
    },
    {
        "canonical_name": "Microsoft Azure",
        "category": "Cloud Platform",
        "variants": ["azure"],
        "typical_years_min": 0,
        "typical_years_max": 12
    },
    
    # DevOps & Tools
    {
        "canonical_name": "Docker",
        "category": "DevOps",
        "variants": [],
        "typical_years_min": 0,
        "typical_years_max": 10
    },
    {
        "canonical_name": "Kubernetes",
        "category": "DevOps",
        "variants": ["k8s", "k8"],
        "typical_years_min": 0,
        "typical_years_max": 8
    },
    {
        "canonical_name": "Git",
        "category": "Version Control",
        "variants": ["github", "gitlab", "bitbucket"],
        "typical_years_min": 0,
        "typical_years_max": 15
    },
    {
        "canonical_name": "CI/CD",
        "category": "DevOps",
        "variants": ["cicd", "continuous integration", "continuous deployment"],
        "typical_years_min": 0,
        "typical_years_max": 12
    },
    {
        "canonical_name": "Jenkins",
        "category": "DevOps",
        "variants": [],
        "typical_years_min": 0,
        "typical_years_max": 12
    },
    {
        "canonical_name": "Terraform",
        "category": "DevOps",
        "variants": [],
        "typical_years_min": 0,
        "typical_years_max": 8
    },
    {
        "canonical_name": "Ansible",
        "category": "DevOps",
        "variants": [],
        "typical_years_min": 0,
        "typical_years_max": 10
    },
    
    # Testing
    {
        "canonical_name": "Jest",
        "category": "Testing",
        "variants": [],
        "typical_years_min": 0,
        "typical_years_max": 6
    },
    {
        "canonical_name": "Pytest",
        "category": "Testing",
        "variants": ["py.test"],
        "typical_years_min": 0,
        "typical_years_max": 10
    },
    {
        "canonical_name": "JUnit",
        "category": "Testing",
        "variants": [],
        "typical_years_min": 0,
        "typical_years_max": 15
    },
    
    # AI/ML
    {
        "canonical_name": "Machine Learning",
        "category": "AI/ML",
        "variants": ["ml"],
        "typical_years_min": 0,
        "typical_years_max": 10
    },
    {
        "canonical_name": "Deep Learning",
        "category": "AI/ML",
        "variants": ["dl"],
        "typical_years_min": 0,
        "typical_years_max": 8
    },
    {
        "canonical_name": "TensorFlow",
        "category": "AI/ML",
        "variants": ["tf"],
        "typical_years_min": 0,
        "typical_years_max": 8
    },
    {
        "canonical_name": "PyTorch",
        "category": "AI/ML",
        "variants": ["torch"],
        "typical_years_min": 0,
        "typical_years_max": 7
    },
    {
        "canonical_name": "scikit-learn",
        "category": "AI/ML",
        "variants": ["sklearn", "scikit learn"],
        "typical_years_min": 0,
        "typical_years_max": 10
    },
]


def seed_skills(db: Session):
    """Seed canonical skills and their variants."""
    print("=" * 60)
    print("SEEDING SKILLS")
    print("=" * 60)
    
    skills_created = 0
    variants_created = 0
    skills_skipped = 0
    
    for skill_data in SKILLS_DATA:
        canonical_name = skill_data["canonical_name"]
        
        # Check if skill already exists
        existing_skill = db.query(Skill).filter(
            Skill.canonical_name == canonical_name
        ).first()
        
        if existing_skill:
            print(f"[-] Skill already exists: {canonical_name}")
            skills_skipped += 1
            continue
        
        # Create skill
        skill = Skill(
            canonical_name=canonical_name,
            category=skill_data.get("category"),
            typical_years_min=skill_data.get("typical_years_min"),
            typical_years_max=skill_data.get("typical_years_max")
        )
        db.add(skill)
        db.flush()  # Get the ID
        
        print(f"[+] Created skill: {canonical_name} ({skill_data.get('category')})")
        skills_created += 1
        
        # Create variants
        for variant_name in skill_data.get("variants", []):
            # Check if variant already exists
            existing_variant = db.query(SkillVariant).filter(
                SkillVariant.variant_name == variant_name
            ).first()
            
            if existing_variant:
                print(f"    [-] Variant already exists: {variant_name}")
                continue
            
            variant = SkillVariant(
                skill_id=skill.id,
                variant_name=variant_name
            )
            db.add(variant)
            print(f"    [+] Added variant: {variant_name}")
            variants_created += 1
    
    db.commit()
    
    print("=" * 60)
    print(f"SEEDING COMPLETE")
    print(f"  Skills created: {skills_created}")
    print(f"  Skills skipped: {skills_skipped}")
    print(f"  Variants created: {variants_created}")
    print(f"  Total skills in DB: {db.query(Skill).count()}")
    print("=" * 60)


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_skills(db)
    except Exception as e:
        print(f"[!] Error seeding skills: {e}")
        db.rollback()
        raise
    finally:
        db.close()

# Made with Bob
