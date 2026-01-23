# EasyHire-Scout

Built an AI‑powered FastAPI platform that scrapes European tech job postings, stores them in PostgreSQL, and matches them to my profile using a local LLM (Llama via Ollama).

## Installation

### Prerequisites

- Python 3.10 or higher
- PostgreSQL database (for storing job postings)
- Ollama installed and running locally (for LLM functionality)

### Step-by-Step Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd EasyHire-Scout
   ```

2. **Create a virtual environment**
   ```bash
   python3.12 -m venv venv
   ```

3. **Activate the virtual environment**
   
   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```
   
   On Windows:
   ```bash
   venv\Scripts\activate
   ```

4. **Install the package**
   ```bash
   pip install .
   ```

5. **Install optional dependencies (for embeddings support)**
   ```bash
   pip install .[embeddings]
   ```

6. **Set up environment variables**
   
   Create a `.env` file in the project root with your configuration:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/easyhire_scout [Your choice in naming, I only added the fundamental format for PostgreSQL URL]
   OLLAMA_BASE_URL=http://localhost:11434
   ```

7. **Verify installation**
   ```bash
   pip list | grep easyhire-scout
   ```

## Dependencies

For detailed information about why each package is used in this project, see [DEPENDENCIES.md](DEPENDENCIES.md).

## Database Schema

The database follows a 3NF normalized design with 12 core tables. The Entity Relationship Diagram (ERD) below illustrates the complete database structure:

![EasyHire Scout - Stage 1 Database Schema](docs/easyhire_stage_1_ERD.png)

**Database Tables:**
- **Core entities**: `companies`, `locations`, `job_categories`
- **Scraping tracking**: `scrape_sites`, `scrape_runs`, `scrape_errors`
- **Jobs**: `jobs`, `job_languages`
- **Skills**: `skills`, `skill_variants`
- **Junction tables**: `job_categories_link`, `job_skills`

The SQLAlchemy models are defined in `easyhire_scout/models.py` and match the PostgreSQL schema exactly. To initialize the database, run:

```bash
python scripts/init_db.py
```
