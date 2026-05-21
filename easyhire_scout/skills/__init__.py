"""
Skills module for EasyHire Scout.

This module handles skill matching using a three-tier approach:
1. Exact match (normalized string lookup)
2. Fuzzy match (RapidFuzz similarity)
3. LLM match (DeepSeek API for semantic matching)
"""

from easyhire_scout.skills.skill_matcher import SkillMatcherService, MatchResult
from easyhire_scout.skills.exceptions import (
    SkillMatchError,
    LLMAPIError,
    LLMTimeoutError,
    SkillNotFoundError,
)

__all__ = [
    "SkillMatcherService",
    "MatchResult",
    "SkillMatchError",
    "LLMAPIError",
    "LLMTimeoutError",
    "SkillNotFoundError",
]

# Made with Bob
