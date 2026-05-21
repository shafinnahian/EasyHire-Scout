"""
Typed exception hierarchy for skill matching operations.
Follows fullstack-dev Section 3: Error Handling & Resilience.
"""


class SkillMatchError(Exception):
    """Base exception for skill matching errors."""
    
    def __init__(self, message: str, code: str, is_retryable: bool = False):
        """
        Initialize skill match error.
        
        Args:
            message: Human-readable error message
            code: Machine-readable error code (e.g., "LLM_API_ERROR")
            is_retryable: Whether the operation should be retried
        """
        self.message = message
        self.code = code
        self.is_retryable = is_retryable
        super().__init__(message)


class LLMAPIError(SkillMatchError):
    """DeepSeek API call failed."""
    
    def __init__(self, status_code: int, response: dict):
        """
        Initialize LLM API error.
        
        Args:
            status_code: HTTP status code from API
            response: Response body from API
        """
        # Retry only on 5xx server errors and 429 rate limits
        is_retryable = (500 <= status_code < 600) or status_code == 429
        
        super().__init__(
            message=f"LLM API error: {status_code}",
            code="LLM_API_ERROR",
            is_retryable=is_retryable
        )
        self.status_code = status_code
        self.response = response


class LLMTimeoutError(SkillMatchError):
    """LLM request timed out."""
    
    def __init__(self):
        """Initialize LLM timeout error."""
        super().__init__(
            message="LLM request timed out",
            code="LLM_TIMEOUT",
            is_retryable=True  # Timeouts are transient, retry
        )


class SkillNotFoundError(SkillMatchError):
    """No matching skill found in any tier."""
    
    def __init__(self, raw_skill: str):
        """
        Initialize skill not found error.
        
        Args:
            raw_skill: The raw skill string that couldn't be matched
        """
        super().__init__(
            message=f"No match found for skill: {raw_skill}",
            code="SKILL_NOT_FOUND",
            is_retryable=False  # Not found is permanent, don't retry
        )
        self.raw_skill = raw_skill


class InvalidSkillInputError(SkillMatchError):
    """Invalid input provided for skill matching."""
    
    def __init__(self, reason: str):
        """
        Initialize invalid input error.
        
        Args:
            reason: Explanation of why input is invalid
        """
        super().__init__(
            message=f"Invalid skill input: {reason}",
            code="INVALID_INPUT",
            is_retryable=False
        )

# Made with Bob
