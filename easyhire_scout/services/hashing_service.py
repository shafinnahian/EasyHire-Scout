import hashlib
import json
from typing import Any, Dict, List

class HashingService:
    """
    Service responsible for the Canonical Hashing Protocol.
    Ensures search criteria are deterministic and unique.
    """

    @staticmethod
    def canonicalize(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively normalizes a dictionary/list for deterministic hashing.
        1. Strips and lowercases strings.
        2. Sorts lists.
        3. Sorts dictionary keys.
        """
        if isinstance(data, dict):
            # Sort keys and recursively canonicalize values
            return {
                k.lower().strip(): HashingService.canonicalize(v)
                for k, v in sorted(data.items())
                if v is not None  # Exclude nulls to keep hash stable across schema updates
            }
        elif isinstance(data, list):
            # Sort lists to ensure order doesn't change the hash
            items = [HashingService.canonicalize(item) for item in data]
            # Only sort if items are sortable (e.g., all strings or all same-type dicts)
            try:
                return sorted(items, key=lambda x: str(x))
            except Exception:
                return items
        elif isinstance(data, str):
            return data.lower().strip()
        return data

    @classmethod
    def generate_cohort_hash(cls, criteria: Dict[str, Any]) -> str:
        """
        Generates a SHA-256 hash from a canonicalized criteria dictionary.
        """
        # 1. Prune non-intent fields (like 'message', 'language_strict') if necessary
        # For now, we assume the input is already filtered by the schema
        
        # 2. Canonicalize
        canonical_data = cls.canonicalize(criteria)
        
        # 3. Create deterministic JSON string
        json_str = json.dumps(canonical_data, sort_keys=True)
        
        # 4. Hash
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()
