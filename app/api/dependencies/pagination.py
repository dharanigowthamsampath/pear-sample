from typing import Optional, Dict, Any, Tuple
from fastapi import Query


class Pagination:
    """Pagination parameters for API endpoints."""
    
    def __init__(
        self, 
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Number of items per page")
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size
    
    def get_pagination_params(self) -> Dict[str, Any]:
        """Return parameters for pagination queries."""
        return {
            "limit": self.page_size,
            "offset": self.offset
        }
    
    def get_pagination_query(self) -> str:
        """Return SQL fragment for pagination."""
        return "LIMIT :limit OFFSET :offset"
    
    def paginate_response(self, items: list, total: int) -> Dict[str, Any]:
        """
        Create a paginated response.
        
        Args:
            items: List of items for the current page
            total: Total number of items
            
        Returns:
            Dictionary with pagination metadata and items
        """
        total_pages = (total + self.page_size - 1) // self.page_size
        
        return {
            "items": items,
            "pagination": {
                "page": self.page,
                "page_size": self.page_size,
                "total_items": total,
                "total_pages": total_pages,
                "has_previous": self.page > 1,
                "has_next": self.page < total_pages
            }
        }
    
    def get_count_and_paginate(
        self, 
        query: str, 
        count_query: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Create count and paginated queries.
        
        Args:
            query: Base SQL query
            count_query: Optional custom count query
            
        Returns:
            Tuple of (count query, paginated query)
        """
        if count_query is None:
            count_query = f"SELECT COUNT(*) FROM ({query}) AS count_query"
            
        paginated_query = f"{query} {self.get_pagination_query()}"
        
        return count_query, paginated_query