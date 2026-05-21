"""
Pydantic schemas for skill matching and LLM interactions.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class MatchResult(BaseModel):
    """Result of a skill matching operation."""
    
    raw_input: str = Field(description="Original skill string provided")
    skill_id: Optional[int] = Field(default=None, description="Matched canonical skill ID")
    skill_name: Optional[str] = Field(default=None, description="Matched canonical skill name")
    confidence: float = Field(ge=0.0, le=1.0, description="Match confidence score (0.0-1.0)")
    tier_used: str = Field(description="Matching tier: 'exact', 'fuzzy', 'llm', or 'none'")
    needs_review: bool = Field(default=False, description="Whether match needs human review")
    reasoning: Optional[str] = Field(default=None, description="Explanation of match decision")
    
    @field_validator('tier_used')
    @classmethod
    def validate_tier(cls, v: str) -> str:
        """Validate tier_used is one of the allowed values."""
        allowed = {'exact', 'fuzzy', 'llm', 'none'}
        if v not in allowed:
            raise ValueError(f"tier_used must be one of {allowed}")
        return v
    
    class Config:
        from_attributes = True


class LLMMatchRequest(BaseModel):
    """Request schema for LLM skill matching."""
    
    raw_skill: str = Field(description="Raw skill string to match")
    candidate_skills: List[str] = Field(
        description="List of canonical skill names to match against",
        min_length=1,
        max_length=50  # Limit to avoid token overflow
    )
    
    @field_validator('raw_skill')
    @classmethod
    def validate_raw_skill(cls, v: str) -> str:
        """Validate raw skill is not empty."""
        if not v or not v.strip():
            raise ValueError("raw_skill cannot be empty")
        return v.strip()


class LLMMatchResponse(BaseModel):
    """Response schema from LLM skill matching."""
    
    matched_skill: Optional[str] = Field(
        default=None,
        description="Matched canonical skill name (null if no match)"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0)"
    )
    reasoning: str = Field(description="Explanation of match decision")
    
    @field_validator('matched_skill')
    @classmethod
    def validate_matched_skill(cls, v: Optional[str]) -> Optional[str]:
        """Validate matched skill if provided."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class SkillExtractionRequest(BaseModel):
    """Request schema for extracting skills from job description."""
    
    job_title: str = Field(description="Job title")
    job_description: str = Field(description="Full job description text")
    requirements: Optional[str] = Field(default=None, description="Requirements section")
    
    @field_validator('job_description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate description is not empty."""
        if not v or not v.strip():
            raise ValueError("job_description cannot be empty")
        return v.strip()


class SkillExtractionResponse(BaseModel):
    """Response schema from LLM skill extraction."""
    
    skills: List[str] = Field(
        description="List of extracted skill names",
        default_factory=list
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall extraction confidence"
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="Explanation of extraction decisions"
    )


class BatchMatchRequest(BaseModel):
    """Request schema for batch skill matching."""
    
    raw_skills: List[str] = Field(
        description="List of raw skill strings to match",
        min_length=1,
        max_length=100  # Reasonable batch size
    )
    use_llm: bool = Field(
        default=True,
        description="Whether to use LLM for unmatched skills"
    )
    
    @field_validator('raw_skills')
    @classmethod
    def validate_skills(cls, v: List[str]) -> List[str]:
        """Validate and clean skill list."""
        # Remove empty strings and duplicates while preserving order
        seen = set()
        cleaned = []
        for skill in v:
            skill = skill.strip()
            if skill and skill.lower() not in seen:
                cleaned.append(skill)
                seen.add(skill.lower())
        
        if not cleaned:
            raise ValueError("raw_skills must contain at least one non-empty skill")
        
        return cleaned


class BatchMatchResponse(BaseModel):
    """Response schema for batch skill matching."""
    
    results: List[MatchResult] = Field(description="Match results for each skill")
    total_processed: int = Field(description="Total number of skills processed")
    tier_stats: dict = Field(
        description="Statistics by tier",
        default_factory=lambda: {"exact": 0, "fuzzy": 0, "llm": 0, "none": 0}
    )
    duration_ms: float = Field(description="Processing duration in milliseconds")

# Made with Bob
