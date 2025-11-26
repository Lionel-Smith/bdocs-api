from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, Any, List
from datetime import datetime

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper"""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = False
    error: str
    message: str
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper"""
    success: bool = True
    data: List[T]
    pagination: dict = Field(
        description="Pagination metadata",
        examples=[{
            "page": 1,
            "page_size": 20,
            "total_items": 100,
            "total_pages": 5
        }]
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @staticmethod
    def create(
        data: List[T],
        page: int,
        page_size: int,
        total_items: int
    ) -> 'PaginatedResponse[T]':
        """Helper to create paginated response"""
        total_pages = (total_items + page_size - 1) // page_size

        return PaginatedResponse(
            data=data,
            pagination={
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages
            }
        )
