"""
Search DTOs - Data Transfer Objects for inmate search functionality.

Provides structured search criteria, paginated results, and saved search management.
"""
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from src.common.enums import InmateStatus, SecurityLevel, Gender


# =============================================================================
# Search Criteria DTOs
# =============================================================================

class InmateSearchCriteriaDTO(BaseModel):
    """
    Search criteria for inmate queries.

    Supports:
    - Full-text search on name and booking_number
    - Multiple filter combinations
    - Date ranges
    - Age ranges
    """
    model_config = ConfigDict(from_attributes=True)

    # Full-text search query
    query: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Search query for name or booking number"
    )

    # Status filters
    status: Optional[InmateStatus] = Field(
        None,
        description="Filter by inmate status"
    )
    statuses: Optional[List[InmateStatus]] = Field(
        None,
        description="Filter by multiple statuses"
    )

    # Classification filters
    security_level: Optional[SecurityLevel] = Field(
        None,
        description="Filter by security level"
    )
    security_levels: Optional[List[SecurityLevel]] = Field(
        None,
        description="Filter by multiple security levels"
    )

    # Demographics
    gender: Optional[Gender] = Field(
        None,
        description="Filter by gender"
    )
    nationality: Optional[str] = Field(
        None,
        max_length=100,
        description="Filter by nationality"
    )
    island_of_origin: Optional[str] = Field(
        None,
        max_length=50,
        description="Filter by Bahamian island of origin"
    )

    # Date range filters
    admission_date_from: Optional[date] = Field(
        None,
        description="Admission date range start"
    )
    admission_date_to: Optional[date] = Field(
        None,
        description="Admission date range end"
    )

    # Age range filters
    age_min: Optional[int] = Field(
        None,
        ge=0,
        le=120,
        description="Minimum age filter"
    )
    age_max: Optional[int] = Field(
        None,
        ge=0,
        le=120,
        description="Maximum age filter"
    )

    # Housing filter
    current_housing_unit: Optional[str] = Field(
        None,
        max_length=50,
        description="Filter by current housing unit"
    )

    # Include released inmates
    include_released: bool = Field(
        False,
        description="Include released inmates in results"
    )


class SearchSortDTO(BaseModel):
    """Sort configuration for search results."""
    model_config = ConfigDict(from_attributes=True)

    field: str = Field(
        "last_name",
        description="Field to sort by: last_name, admission_date, date_of_birth"
    )
    direction: str = Field(
        "asc",
        pattern="^(asc|desc)$",
        description="Sort direction: asc or desc"
    )


class PaginationDTO(BaseModel):
    """Pagination parameters."""
    model_config = ConfigDict(from_attributes=True)

    page: int = Field(
        1,
        ge=1,
        description="Page number (1-based)"
    )
    page_size: int = Field(
        25,
        ge=1,
        le=100,
        description="Results per page (max 100)"
    )


# =============================================================================
# Search Result DTOs
# =============================================================================

class InmateSearchResultDTO(BaseModel):
    """
    Single inmate result with computed fields.

    Includes calculated values for age, full_name, days_in_custody,
    and current housing assignment.
    """
    model_config = ConfigDict(from_attributes=True)

    # Core identifiers
    id: UUID
    booking_number: str
    nib_number: Optional[str] = None

    # Name fields
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    full_name: str  # Computed: "Last, First Middle"

    # Demographics
    date_of_birth: date
    age: int  # Computed from date_of_birth
    gender: Gender
    nationality: str
    island_of_origin: Optional[str] = None

    # Physical description
    photo_url: Optional[str] = None

    # Classification
    status: InmateStatus
    security_level: SecurityLevel

    # Dates
    admission_date: datetime
    release_date: Optional[datetime] = None
    days_in_custody: int  # Computed

    # Current housing
    current_housing: Optional[str] = None  # From active HousingAssignment


class PaginatedSearchResultDTO(BaseModel):
    """Paginated search results with metadata."""
    model_config = ConfigDict(from_attributes=True)

    # Results
    items: List[InmateSearchResultDTO]

    # Pagination metadata
    total: int = Field(description="Total matching records")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Results per page")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_previous: bool = Field(description="Whether there is a previous page")

    # Search metadata
    query: Optional[str] = Field(None, description="Original search query")
    filters_applied: int = Field(0, description="Number of filters applied")
    search_time_ms: float = Field(description="Search execution time in milliseconds")


# =============================================================================
# Saved Search DTOs
# =============================================================================

class SavedSearchCreateDTO(BaseModel):
    """Create a saved search."""
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name for this saved search"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional description"
    )
    criteria: InmateSearchCriteriaDTO = Field(
        ...,
        description="Search criteria to save"
    )
    is_shared: bool = Field(
        False,
        description="Whether this search is shared with other users"
    )


class SavedSearchUpdateDTO(BaseModel):
    """Update a saved search."""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100
    )
    description: Optional[str] = Field(
        None,
        max_length=500
    )
    criteria: Optional[InmateSearchCriteriaDTO] = None
    is_shared: Optional[bool] = None


class SavedSearchDTO(BaseModel):
    """Saved search response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: Optional[str] = None
    criteria: dict  # JSON representation of search criteria
    is_shared: bool

    # Ownership
    created_by: UUID
    created_by_name: Optional[str] = None

    # Usage stats
    use_count: int
    last_used_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None


# =============================================================================
# Recent Search DTOs
# =============================================================================

class RecentSearchDTO(BaseModel):
    """Recent search record."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    query: Optional[str] = None
    criteria: dict  # JSON representation
    result_count: int
    searched_at: datetime


# =============================================================================
# Search Suggestion DTOs
# =============================================================================

class SearchSuggestionDTO(BaseModel):
    """Autocomplete suggestion."""
    model_config = ConfigDict(from_attributes=True)

    text: str = Field(description="Suggested text")
    type: str = Field(description="Type: name, booking_number, alias")
    match_count: int = Field(description="Number of matches")


class SuggestionsResponseDTO(BaseModel):
    """Search suggestions response."""
    model_config = ConfigDict(from_attributes=True)

    query: str
    suggestions: List[SearchSuggestionDTO]


# =============================================================================
# Quick Stats DTO
# =============================================================================

class SearchStatsDTO(BaseModel):
    """Quick statistics for search context."""
    model_config = ConfigDict(from_attributes=True)

    total_inmates: int
    by_status: dict  # Status -> count
    by_security_level: dict  # Level -> count
    by_gender: dict  # Gender -> count
