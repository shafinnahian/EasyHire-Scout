"""
Skill Matcher Service - Three-Tier Matching System.

Tier 1: Exact match (normalized string lookup) - O(1), <1ms
Tier 2: Fuzzy match (RapidFuzz similarity) - O(n), <10ms
Tier 3: LLM match (DeepSeek API) - O(API_latency), <2s

Follows fullstack-dev best practices:
- Service layer pattern (no HTTP types)
- Structured logging
- Typed errors
- Graceful degradation
"""

import logging
import time
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_
from rapidfuzz import fuzz, process

from easyhire_scout.models import Skill, SkillVariant
from easyhire_scout.skills.skill_normalizer import SkillNormalizer
from easyhire_scout.skills.schemas import MatchResult
from easyhire_scout.skills.exceptions import InvalidSkillInputError, SkillNotFoundError
from easyhire_scout.core.config import settings

logger = logging.getLogger(__name__)


class SkillMatcherService:
    """
    Service for matching raw skill strings to canonical skill IDs.
    
    Uses a three-tier cascade:
    1. Exact match on normalized strings
    2. Fuzzy match using RapidFuzz
    3. LLM semantic match (implemented in Phase 4)
    """
    
    # Confidence thresholds
    EXACT_MATCH_CONFIDENCE = 1.0
    VARIANT_MATCH_CONFIDENCE = 0.95
    FUZZY_THRESHOLD = 85  # Minimum fuzzy score (0-100)
    FUZZY_HIGH_CONFIDENCE = 0.90  # Score >= 95
    FUZZY_MEDIUM_CONFIDENCE = 0.85  # Score >= 85
    REVIEW_THRESHOLD = 0.85  # Below this, needs human review
    
    @staticmethod
    def match_skills(
        db: Session,
        raw_skills: List[str],
        use_llm: bool = True
    ) -> List[MatchResult]:
        """
        Match multiple raw skill strings to canonical skills.
        
        Args:
            db: Database session
            raw_skills: List of raw skill strings
            use_llm: Whether to use LLM for Tier 3 (default: True)
            
        Returns:
            List of MatchResult objects
            
        Example:
            >>> results = SkillMatcherService.match_skills(db, ["Python", "React.js", "ML"])
            >>> for r in results:
            ...     print(f"{r.raw_input} -> {r.skill_name} (confidence: {r.confidence})")
        """
        start_time = time.time()
        
        logger.info("Starting skill matching", extra={
            "skill_count": len(raw_skills),
            "use_llm": use_llm,
            "operation": "skill_match"
        })
        
        results = []
        tier_stats = {"exact": 0, "fuzzy": 0, "llm": 0, "none": 0}
        
        for raw_skill in raw_skills:
            try:
                result = SkillMatcherService._match_single(db, raw_skill, use_llm)
                results.append(result)
                tier_stats[result.tier_used] += 1
            except Exception as e:
                logger.error(f"Error matching skill '{raw_skill}': {e}", extra={
                    "raw_skill": raw_skill,
                    "error": str(e)
                })
                # Graceful degradation: return no-match result
                results.append(MatchResult(
                    raw_input=raw_skill,
                    skill_id=None,
                    skill_name=None,
                    confidence=0.0,
                    tier_used="none",
                    needs_review=True,
                    reasoning=f"Error during matching: {str(e)}"
                ))
                tier_stats["none"] += 1
        
        duration_ms = (time.time() - start_time) * 1000
        
        logger.info("Skill matching completed", extra={
            "skill_count": len(raw_skills),
            "duration_ms": duration_ms,
            "tier_stats": tier_stats,
            "operation": "skill_match"
        })
        
        return results
    
    @staticmethod
    def _match_single(
        db: Session,
        raw_skill: str,
        use_llm: bool = True
    ) -> MatchResult:
        """
        Match a single skill through the three-tier cascade.
        
        Args:
            db: Database session
            raw_skill: Raw skill string
            use_llm: Whether to use LLM for Tier 3
            
        Returns:
            MatchResult object
        """
        # Validate input
        if not SkillNormalizer.is_valid_skill(raw_skill):
            raise InvalidSkillInputError(f"Invalid skill string: '{raw_skill}'")
        
        # Normalize the input
        normalized = SkillNormalizer.normalize(raw_skill)
        
        # Tier 1: Exact match
        result = SkillMatcherService._tier1_exact_match(db, normalized, raw_skill)
        if result:
            return result
        
        # Tier 2: Fuzzy match
        result = SkillMatcherService._tier2_fuzzy_match(db, normalized, raw_skill)
        if result:
            return result
        
        # Tier 3: LLM match
        if use_llm and settings.ENABLE_LLM_MATCHING:
            result = SkillMatcherService._tier3_llm_match(db, normalized, raw_skill)
            if result:
                return result
        
        # No match found
        logger.warning(f"No match found for skill: {raw_skill}", extra={
            "raw_skill": raw_skill,
            "normalized": normalized
        })
        
        return MatchResult(
            raw_input=raw_skill,
            skill_id=None,
            skill_name=None,
            confidence=0.0,
            tier_used="none",
            needs_review=True,
            reasoning="No match found in any tier"
        )
    
    @staticmethod
    def _tier1_exact_match(
        db: Session,
        normalized: str,
        raw_skill: str
    ) -> Optional[MatchResult]:
        """
        Tier 1: Exact match on normalized canonical name or variant.
        
        Args:
            db: Database session
            normalized: Normalized skill string
            raw_skill: Original raw skill string
            
        Returns:
            MatchResult if found, None otherwise
        """
        # Try exact match on canonical name
        skill = db.query(Skill).filter(
            Skill.canonical_name == normalized
        ).first()
        
        if skill:
            logger.debug(f"Tier 1 exact match: {raw_skill} -> {skill.canonical_name}")
            return MatchResult(
                raw_input=raw_skill,
                skill_id=skill.id,
                skill_name=skill.canonical_name,
                confidence=SkillMatcherService.EXACT_MATCH_CONFIDENCE,
                tier_used="exact",
                needs_review=False,
                reasoning="Exact match on canonical name"
            )
        
        # Try exact match on variant
        variant = db.query(SkillVariant).filter(
            SkillVariant.variant_name == normalized
        ).first()
        
        if variant:
            skill = db.query(Skill).filter(Skill.id == variant.skill_id).first()
            if skill:
                logger.debug(f"Tier 1 variant match: {raw_skill} -> {skill.canonical_name}")
                return MatchResult(
                    raw_input=raw_skill,
                    skill_id=skill.id,
                    skill_name=skill.canonical_name,
                    confidence=SkillMatcherService.VARIANT_MATCH_CONFIDENCE,
                    tier_used="exact",
                    needs_review=False,
                    reasoning=f"Exact match on variant '{variant.variant_name}'"
                )
        
        return None
    
    @staticmethod
    def _tier2_fuzzy_match(
        db: Session,
        normalized: str,
        raw_skill: str
    ) -> Optional[MatchResult]:
        """
        Tier 2: Fuzzy match using RapidFuzz token_set_ratio.
        
        Args:
            db: Database session
            normalized: Normalized skill string
            raw_skill: Original raw skill string
            
        Returns:
            MatchResult if score >= threshold, None otherwise
        """
        # Get all canonical skills
        all_skills = db.query(Skill).all()
        
        if not all_skills:
            logger.warning("No skills in database for fuzzy matching")
            return None
        
        # Create list of (canonical_name, skill_object) tuples
        skill_names = [(skill.canonical_name, skill) for skill in all_skills]
        
        # Use RapidFuzz to find best match
        # token_set_ratio handles word order variations
        best_match = process.extractOne(
            normalized,
            [name for name, _ in skill_names],
            scorer=fuzz.token_set_ratio,
            score_cutoff=SkillMatcherService.FUZZY_THRESHOLD
        )
        
        if not best_match:
            return None
        
        matched_name, score, _ = best_match
        
        # Find the skill object
        matched_skill = next(skill for name, skill in skill_names if name == matched_name)
        
        # Calculate confidence based on score
        if score >= 95:
            confidence = SkillMatcherService.FUZZY_HIGH_CONFIDENCE
            needs_review = False
        else:
            confidence = SkillMatcherService.FUZZY_MEDIUM_CONFIDENCE
            needs_review = True  # Lower scores need review
        
        logger.debug(f"Tier 2 fuzzy match: {raw_skill} -> {matched_skill.canonical_name} (score: {score})")
        
        return MatchResult(
            raw_input=raw_skill,
            skill_id=matched_skill.id,
            skill_name=matched_skill.canonical_name,
            confidence=confidence,
            tier_used="fuzzy",
            needs_review=needs_review,
            reasoning=f"Fuzzy match with score {score}/100"
        )
    
    @staticmethod
    def get_all_skills(db: Session) -> List[Skill]:
        """
        Get all canonical skills from database.
        
        Args:
            db: Database session
            
        Returns:
            List of Skill objects
        """
        return db.query(Skill).order_by(Skill.canonical_name).all()
    
    @staticmethod
    def get_skill_by_id(db: Session, skill_id: int) -> Optional[Skill]:
        """
        Get a skill by ID.
        
        Args:
            db: Database session
            skill_id: Skill ID
            
        Returns:
            Skill object or None
        """
        return db.query(Skill).filter(Skill.id == skill_id).first()
    
    @staticmethod
    def get_skill_variants(db: Session, skill_id: int) -> List[SkillVariant]:
        """
        Get all variants for a skill.
        
        Args:
            db: Database session
            skill_id: Skill ID
            
        Returns:
            List of SkillVariant objects
        """
        return db.query(SkillVariant).filter(
            SkillVariant.skill_id == skill_id
        ).all()

# Made with Bob

    
    @staticmethod
    def _tier3_llm_match(
        db: Session,
        normalized: str,
        raw_skill: str
    ) -> Optional[MatchResult]:
        """
        Tier 3: LLM semantic match using DeepSeek API.
        
        Args:
            db: Database session
            normalized: Normalized skill string
            raw_skill: Original raw skill string
            
        Returns:
            MatchResult if LLM finds a match, None otherwise
        """
        from easyhire_scout.skills.llm_client import DeepSeekClient
        from easyhire_scout.skills.exceptions import LLMAPIError, LLMTimeoutError
        
        try:
            # Get top 20 most common skills as candidates
            # This limits token usage and improves accuracy
            all_skills = db.query(Skill).limit(50).all()
            
            if not all_skills:
                logger.warning("No skills in database for LLM matching")
                return None
            
            candidate_names = [skill.canonical_name for skill in all_skills]
            
            # Call LLM
            client = DeepSeekClient()
            llm_response = client.match_skill(raw_skill, candidate_names)
            
            # Check if LLM found a match
            if not llm_response.matched_skill:
                logger.debug(f"LLM found no match for: {raw_skill}")
                return None
            
            # Find the matched skill in database
            matched_skill = db.query(Skill).filter(
                Skill.canonical_name == llm_response.matched_skill
            ).first()
            
            if not matched_skill:
                logger.warning(f"LLM matched to non-existent skill: {llm_response.matched_skill}")
                return None
            
            # Determine if needs review based on confidence
            needs_review = llm_response.confidence < SkillMatcherService.REVIEW_THRESHOLD
            
            logger.info(f"Tier 3 LLM match: {raw_skill} -> {matched_skill.canonical_name}", extra={
                "raw_skill": raw_skill,
                "matched_skill": matched_skill.canonical_name,
                "confidence": llm_response.confidence,
                "needs_review": needs_review
            })
            
            return MatchResult(
                raw_input=raw_skill,
                skill_id=matched_skill.id,
                skill_name=matched_skill.canonical_name,
                confidence=llm_response.confidence,
                tier_used="llm",
                needs_review=needs_review,
                reasoning=llm_response.reasoning
            )
            
        except (LLMAPIError, LLMTimeoutError) as e:
            logger.error(f"LLM matching failed for '{raw_skill}': {e}", extra={
                "raw_skill": raw_skill,
                "error_code": e.code,
                "is_retryable": e.is_retryable
            })
            # Graceful degradation: return None to indicate no match
            return None
        except Exception as e:
            logger.error(f"Unexpected error in LLM matching: {e}", extra={
                "raw_skill": raw_skill,
                "error": str(e)
            })
            return None
