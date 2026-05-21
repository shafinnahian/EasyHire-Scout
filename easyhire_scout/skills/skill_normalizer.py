"""
Text normalization utilities for skill matching.
Implements multi-stage normalization pipeline for consistent matching.
"""

import re
from typing import Dict, Set


class SkillNormalizer:
    """
    Handles text normalization for skill matching.
    
    Normalization Pipeline:
    1. Lowercase conversion
    2. Remove special characters
    3. Collapse whitespace
    4. Expand common abbreviations
    """
    
    # Common tech skill abbreviations
    # This will be expanded from database SkillVariant table
    ABBREVIATION_MAP: Dict[str, str] = {
        # Programming Languages
        "js": "javascript",
        "ts": "typescript",
        "py": "python",
        "cpp": "c++",
        "cs": "c#",
        "rb": "ruby",
        "go": "golang",
        
        # Frameworks
        "reactjs": "react",
        "vuejs": "vue",
        "nextjs": "next",
        "nuxtjs": "nuxt",
        
        # Databases
        "pg": "postgresql",
        "postgres": "postgresql",
        "mongo": "mongodb",
        
        # Cloud/DevOps
        "k8s": "kubernetes",
        "gcp": "google cloud platform",
        "aws": "amazon web services",
        
        # Tools
        "ci/cd": "cicd",
        "ml": "machine learning",
        "ai": "artificial intelligence",
    }
    
    @staticmethod
    def normalize(text: str) -> str:
        """
        Apply full normalization pipeline to text.
        
        Args:
            text: Raw skill string
            
        Returns:
            Normalized skill string
            
        Example:
            >>> SkillNormalizer.normalize("React.js")
            'react'
            >>> SkillNormalizer.normalize("Node  JS")
            'nodejs'
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Step 1: Lowercase
        normalized = text.lower().strip()
        
        # Step 2: Remove special characters (keep alphanumeric and spaces)
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
        
        # Step 3: Collapse multiple spaces to single space
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Step 4: Remove spaces for compound terms (e.g., "node js" -> "nodejs")
        # This helps with matching variants
        normalized_no_space = normalized.replace(' ', '')
        
        # Step 5: Check abbreviation map
        if normalized_no_space in SkillNormalizer.ABBREVIATION_MAP:
            return SkillNormalizer.ABBREVIATION_MAP[normalized_no_space]
        
        # Return space-collapsed version
        return normalized_no_space
    
    @staticmethod
    def normalize_batch(texts: list[str]) -> list[str]:
        """
        Normalize multiple skill strings.
        
        Args:
            texts: List of raw skill strings
            
        Returns:
            List of normalized skill strings
        """
        return [SkillNormalizer.normalize(text) for text in texts]
    
    @staticmethod
    def extract_tokens(text: str) -> Set[str]:
        """
        Extract individual tokens from skill text for partial matching.
        
        Args:
            text: Skill string
            
        Returns:
            Set of normalized tokens
            
        Example:
            >>> SkillNormalizer.extract_tokens("React Developer")
            {'react', 'developer'}
        """
        normalized = SkillNormalizer.normalize(text)
        # Split on common separators
        tokens = re.split(r'[\s\-_/]+', normalized)
        return {token for token in tokens if token and len(token) > 1}
    
    @staticmethod
    def add_abbreviation(abbreviation: str, canonical: str) -> None:
        """
        Add a new abbreviation to the mapping (for learning from LLM).
        
        Args:
            abbreviation: Short form (e.g., "tf")
            canonical: Full form (e.g., "tensorflow")
        """
        normalized_abbrev = SkillNormalizer.normalize(abbreviation)
        normalized_canonical = SkillNormalizer.normalize(canonical)
        
        if normalized_abbrev and normalized_canonical:
            SkillNormalizer.ABBREVIATION_MAP[normalized_abbrev] = normalized_canonical
    
    @staticmethod
    def is_valid_skill(text: str) -> bool:
        """
        Check if text is a valid skill string.
        
        Args:
            text: Skill string to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not text or not isinstance(text, str):
            return False
        
        normalized = SkillNormalizer.normalize(text)
        
        # Must have at least 2 characters after normalization
        if len(normalized) < 2:
            return False
        
        # Must contain at least one letter
        if not re.search(r'[a-z]', normalized):
            return False
        
        return True

# Made with Bob
