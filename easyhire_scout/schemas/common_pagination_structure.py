"""
Common Pydantic schemas used across the API
"""
from typing import Generic, TypeVar
from pydantic import BaseModel, Field

# Generic type for paginated responses
T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints"""
    page: int = Field(default=1, greaterOrEqual=1, description="Page number (starts at 1)") # page >= 1
    pageSize: int = Field(default=20, greaterOrEqual=1, lessOrEqual=100, description="Items per page (max 100)")
    
    @property
    def skip(self) -> int:
        """Calculate skip value for database queries"""
        return (self.page - 1) * self.pageSize
    
    @property
    def limit(self) -> int:
        """Get limit value"""
        return self.pageSize


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper"""
    items: list[T]
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    pageSize: int = Field(description="Items per page")
    totalPages: int = Field(description="Total number of pages")
    
    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        pageSize: int,
    ) -> "PaginatedResponse[T]":
        """Factory method to create paginated response"""
        totalPages = (total + pageSize - 1) // pageSize if total > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            pageSize=pageSize,
            totalPages=totalPages,
        )


class MessageResponse(BaseModel):
    """Standard message response for simple operations"""
    message: str