from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = ConfigDict(
        from_attributes=True,  # Allow ORM model conversion
        populate_by_name=True,
        use_enum_values=True,
        validate_assignment=True,
        str_strip_whitespace=True
    )


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields matching BaseModel"""
    inserted_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None


class PaginationParams(BaseSchema):
    """Schema for pagination query parameters"""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size
