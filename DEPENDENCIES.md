# Dependencies Explanation

This document explains why each package is used in the EasyHire-Scout project.

## Core Dependencies

### `fastapi>=0.128.0, <0.129.0`
**Purpose**: Modern, fast web framework for building APIs  
**Why**: FastAPI provides automatic API documentation, type validation, and high performance. It's used to create the REST API endpoints for job scraping, storage, and matching operations.

### `uvicorn==0.32.0`
**Purpose**: ASGI server implementation  
**Why**: Uvicorn is the ASGI server that runs the FastAPI application. It provides high-performance async request handling, which is essential for concurrent job scraping and API requests.

### `sqlalchemy==2.0.46`
**Purpose**: SQL toolkit and Object-Relational Mapping (ORM) library  
**Why**: SQLAlchemy provides a Pythonic way to interact with PostgreSQL. It handles database connections, query building, and data modeling, making it easier to manage job postings and user profiles in the database.

### `psycopg2-binary==2.9.10`
**Purpose**: PostgreSQL adapter for Python  
**Why**: This is the database driver that SQLAlchemy uses to communicate with PostgreSQL. The binary version includes pre-compiled binaries, making installation easier without requiring PostgreSQL development libraries.

### `requests>=2.32.5, <3.0.0`
**Purpose**: HTTP library for making web requests  
**Why**: Used for scraping job postings from various European tech job websites. It handles HTTP requests, cookies, headers, and response parsing.

### `beautifulsoup4==4.12.3`
**Purpose**: HTML/XML parser for extracting data from web pages  
**Why**: BeautifulSoup parses HTML content from job posting websites, allowing extraction of job titles, descriptions, requirements, and other relevant information from the scraped pages.

### `ollama==0.4.4`
**Purpose**: Python client for Ollama (local LLM server)  
**Why**: Ollama allows running large language models locally. This package provides the Python interface to communicate with the Ollama server for LLM-based job matching and analysis.

### `langchain==1.2.6`
**Purpose**: Framework for building LLM applications  
**Why**: LangChain provides abstractions for working with LLMs, including prompt templates, chains, and memory. It simplifies the integration of Ollama LLMs for job matching and resume analysis.

### `langchain-community==0.4.1`
**Purpose**: Community integrations for LangChain  
**Why**: Contains community-contributed integrations, including the Ollama integration that connects LangChain with the local Ollama server.

### `pypdf==6.6.0`
**Purpose**: PDF parsing library  
**Why**: Used to extract text from PDF resumes and job descriptions. This enables parsing user-uploaded resumes and PDF job postings for matching.

### `scikit-learn==1.8.0`
**Purpose**: Machine learning library  
**Why**: Provides utilities for text processing, feature extraction, and potentially similarity calculations for job matching. May be used for preprocessing text data before LLM analysis.

### `python-dotenv==1.0.1`
**Purpose**: Load environment variables from `.env` files  
**Why**: Manages configuration settings (database URLs, API keys, etc.) without hardcoding sensitive information. Keeps credentials secure and makes deployment easier.

### `pydantic>=2.12.5,<3.0.0`
**Purpose**: Data validation using Python type annotations  
**Why**: FastAPI uses Pydantic for request/response validation. It ensures data integrity for API endpoints, validates job posting data, and provides clear error messages for invalid inputs.

## Optional Dependencies

### `faiss-cpu==1.9.0.post1`
**Purpose**: Facebook AI Similarity Search library (CPU version)  
**Why**: Provides efficient similarity search and clustering of dense vectors. Used for semantic search and matching job postings to resumes using embeddings, enabling fast retrieval of similar job postings.

### `sentence-transformers==5.2.0`
**Purpose**: Library for generating sentence embeddings  
**Why**: Converts text (job descriptions, resumes) into dense vector representations (embeddings). These embeddings capture semantic meaning, enabling similarity-based matching between job requirements and candidate profiles.

## Dependency Relationships

- **FastAPI + Uvicorn**: FastAPI defines the API, Uvicorn runs it
- **SQLAlchemy + psycopg2-binary**: SQLAlchemy provides ORM, psycopg2-binary connects to PostgreSQL
- **Requests + BeautifulSoup4**: Requests fetches web pages, BeautifulSoup4 parses HTML
- **Ollama + LangChain + langchain-community**: Ollama runs LLMs locally, LangChain provides framework, langchain-community provides integration
- **sentence-transformers + faiss-cpu**: sentence-transformers creates embeddings, faiss-cpu enables fast similarity search
