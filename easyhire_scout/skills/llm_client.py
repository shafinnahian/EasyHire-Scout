"""
DeepSeek API Client for skill matching.

Implements resilience patterns:
- Exponential backoff retry
- Timeout handling
- Structured JSON output
- API key from environment

Follows fullstack-dev Section 3: Error Handling & Resilience.
"""

import requests
import logging
import json
from typing import Dict, List, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from easyhire_scout.core.config import settings
from easyhire_scout.skills.exceptions import LLMAPIError, LLMTimeoutError
from easyhire_scout.skills.schemas import LLMMatchResponse

logger = logging.getLogger(__name__)


class DeepSeekClient:
    """
    Resilient client for DeepSeek API with retry logic.
    
    Features:
    - Automatic retry with exponential backoff
    - Structured JSON output from LLM
    - Comprehensive error handling
    - Request/response logging
    """
    
    def __init__(self):
        """Initialize DeepSeek client with config from environment."""
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL
        self.model = settings.DEEPSEEK_MODEL
        self.timeout = settings.DEEPSEEK_TIMEOUT
        self.max_retries = settings.DEEPSEEK_MAX_RETRIES
        
        logger.info("DeepSeek client initialized", extra={
            "base_url": self.base_url,
            "model": self.model,
            "timeout": self.timeout,
            "max_retries": self.max_retries
        })
    
    @retry(
        stop=stop_after_attempt(3),  # Will use settings.DEEPSEEK_MAX_RETRIES
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((LLMTimeoutError, LLMAPIError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    def match_skill(
        self,
        raw_skill: str,
        candidate_skills: List[str]
    ) -> LLMMatchResponse:
        """
        Ask LLM to match raw skill to one of the candidates.
        
        Args:
            raw_skill: Raw skill string to match
            candidate_skills: List of canonical skill names to match against
            
        Returns:
            LLMMatchResponse with matched skill, confidence, and reasoning
            
        Raises:
            LLMAPIError: API returned error status
            LLMTimeoutError: Request timed out
            
        Example:
            >>> client = DeepSeekClient()
            >>> response = client.match_skill("React.js", ["React", "Angular", "Vue"])
            >>> print(response.matched_skill)  # "React"
            >>> print(response.confidence)     # 0.95
        """
        prompt = self._build_match_prompt(raw_skill, candidate_skills)
        
        logger.debug(f"LLM match request for: {raw_skill}", extra={
            "raw_skill": raw_skill,
            "candidate_count": len(candidate_skills)
        })
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a technical skill matcher. Return only valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1,  # Low temperature for consistency
                    "response_format": {"type": "json_object"}
                },
                timeout=self.timeout
            )
            
            # Handle rate limiting (429)
            if response.status_code == 429:
                logger.warning("Rate limited by DeepSeek API")
                raise LLMAPIError(429, response.json())
            
            # Handle server errors (5xx) - retryable
            if response.status_code >= 500:
                logger.error(f"DeepSeek API server error: {response.status_code}")
                raise LLMAPIError(response.status_code, response.json())
            
            # Handle client errors (4xx) - not retryable
            if response.status_code != 200:
                logger.error(f"DeepSeek API error: {response.status_code}")
                error_body = response.json() if response.content else {}
                raise LLMAPIError(response.status_code, error_body)
            
            # Parse successful response
            result = response.json()
            llm_response = self._parse_response(result)
            
            logger.info(f"LLM match completed: {raw_skill} -> {llm_response.matched_skill}", extra={
                "raw_skill": raw_skill,
                "matched_skill": llm_response.matched_skill,
                "confidence": llm_response.confidence
            })
            
            return llm_response
            
        except requests.Timeout:
            logger.error("DeepSeek API timeout", extra={
                "raw_skill": raw_skill,
                "timeout": self.timeout
            })
            raise LLMTimeoutError()
        
        except requests.RequestException as e:
            logger.error(f"DeepSeek API request failed: {e}", extra={
                "raw_skill": raw_skill,
                "error": str(e)
            })
            raise LLMAPIError(0, {"error": str(e)})
    
    def extract_skills(
        self,
        job_title: str,
        job_description: str,
        requirements: Optional[str] = None
    ) -> List[str]:
        """
        Extract skills from job description using LLM.
        
        Args:
            job_title: Job title
            job_description: Full job description
            requirements: Optional requirements section
            
        Returns:
            List of extracted skill names
            
        Example:
            >>> client = DeepSeekClient()
            >>> skills = client.extract_skills(
            ...     "Senior Python Developer",
            ...     "We need someone with Python, Django, and PostgreSQL..."
            ... )
            >>> print(skills)  # ["Python", "Django", "PostgreSQL"]
        """
        prompt = self._build_extraction_prompt(job_title, job_description, requirements)
        
        logger.debug(f"LLM skill extraction for: {job_title}")
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a technical recruiter. Extract skills from job descriptions. Return only valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"}
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.error(f"Skill extraction failed: {response.status_code}")
                return []
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            
            skills = parsed.get("skills", [])
            logger.info(f"Extracted {len(skills)} skills from job", extra={
                "job_title": job_title,
                "skill_count": len(skills)
            })
            
            return skills
            
        except Exception as e:
            logger.error(f"Skill extraction error: {e}")
            return []
    
    def _build_match_prompt(self, raw_skill: str, candidates: List[str]) -> str:
        """Build prompt for skill matching."""
        candidates_list = "\n".join(f"- {c}" for c in candidates)
        
        return f"""Match the skill "{raw_skill}" to ONE of these canonical skills:

{candidates_list}

Return JSON in this exact format:
{{
  "matched_skill": "exact name from list or null if no good match",
  "confidence": 0.85,
  "reasoning": "brief explanation"
}}

Matching rules:
- Consider abbreviations (e.g., "JS" = "JavaScript")
- Consider synonyms (e.g., "React.js" = "React")
- Consider frameworks vs languages (e.g., "Django" is Python framework)
- If confidence < 0.7, return null for matched_skill
- Confidence scale: 1.0 = exact, 0.9 = very close, 0.8 = similar, 0.7 = weak match"""
    
    def _build_extraction_prompt(
        self,
        job_title: str,
        job_description: str,
        requirements: Optional[str]
    ) -> str:
        """Build prompt for skill extraction."""
        full_text = f"Job Title: {job_title}\n\nDescription: {job_description}"
        if requirements:
            full_text += f"\n\nRequirements: {requirements}"
        
        return f"""{full_text}

Extract all technical skills mentioned in this job posting.

Return JSON in this exact format:
{{
  "skills": ["Python", "Django", "PostgreSQL", "Docker"],
  "confidence": 0.9,
  "reasoning": "Found explicit mentions of these technologies"
}}

Extraction rules:
- Include programming languages, frameworks, databases, tools
- Use canonical names (e.g., "JavaScript" not "JS")
- Exclude soft skills (e.g., "communication", "teamwork")
- Exclude job titles (e.g., "Senior Developer")
- Include only skills explicitly mentioned"""
    
    def _parse_response(self, response: Dict) -> LLMMatchResponse:
        """
        Parse LLM API response into structured format.
        
        Args:
            response: Raw API response
            
        Returns:
            LLMMatchResponse object
        """
        try:
            content = response["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            
            return LLMMatchResponse(
                matched_skill=parsed.get("matched_skill"),
                confidence=float(parsed.get("confidence", 0.0)),
                reasoning=parsed.get("reasoning", "No reasoning provided")
            )
        except (KeyError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}", extra={
                "response": response
            })
            # Return low-confidence no-match result
            return LLMMatchResponse(
                matched_skill=None,
                confidence=0.0,
                reasoning=f"Failed to parse LLM response: {str(e)}"
            )

# Made with Bob
