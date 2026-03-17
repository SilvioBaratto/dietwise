"""Global dependencies for the application"""

import time
from typing import Optional, Annotated, Any
from fastapi import Depends, Request
from sqlalchemy.orm import Session
import logging

from app.exceptions import RateLimitError

logger = logging.getLogger(__name__)

# Database session dependencies - imported from database module
from app.database import get_db


# Import auth dependencies from the auth module
from app.auth.dependencies import (
    get_current_user,
    get_optional_user,
    require_user,
    CurrentUser,
    OptionalUser,
    RequireAuth,
    UserId,
)


class RateLimiter:
    """
    In-memory rate limiting dependency

    Features:
    - Sliding window rate limiting
    - IP-based and user-based limiting
    - Configurable requests per window
    """

    def __init__(self, requests: int = 100, window: int = 60, per_user: bool = False):
        self.requests = requests
        self.window = window
        self.per_user = per_user
        self._in_memory_cache: dict[str, list[float]] = {}

    def __call__(self, request: Request, current_user: Optional[dict] = None):
        """Check rate limit for the request"""
        return self._check_rate_limit(request, current_user)

    def _check_rate_limit(
        self, request: Request, current_user: Optional[dict] = None
    ) -> bool:
        """In-memory rate limiting"""
        # Determine rate limit key
        if self.per_user and current_user:
            key = f"user:{current_user['id']}"
        else:
            key = f"ip:{self._get_client_ip(request)}"

        current_time = time.time()
        window_start = current_time - self.window

        # Clean old entries and check current count
        if key not in self._in_memory_cache:
            self._in_memory_cache[key] = []

        # Remove old entries
        self._in_memory_cache[key] = [
            timestamp
            for timestamp in self._in_memory_cache[key]
            if timestamp > window_start
        ]

        # Check rate limit
        if len(self._in_memory_cache[key]) >= self.requests:
            raise RateLimitError(
                message=f"Rate limit exceeded: {len(self._in_memory_cache[key])}/{self.requests} requests per {self.window}s"
            )

        # Add current request
        self._in_memory_cache[key].append(current_time)
        return True

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers"""
        # Check for forwarded headers (load balancer, proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"


def get_rate_limiter(requests: int = 100, window: int = 60) -> RateLimiter:
    """Factory for rate limiter dependency"""
    return RateLimiter(requests=requests, window=window)


# Common dependency injections
DBSession = Annotated[Session, Depends(get_db)]


class PaginationParams:
    """
    Pagination parameters with cursor support

    Features:
    - Traditional offset/limit pagination
    - Cursor-based pagination for large datasets
    - Configurable limits with safety bounds
    """

    def __init__(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        cursor: Optional[str] = None,
        use_cursor: bool = False,
    ):
        self.skip = max(0, skip)
        self.limit = min(max(1, limit), 1000)  # Max 1000 items for safety
        self.order_by = order_by
        self.order_desc = order_desc
        self.cursor = cursor
        self.use_cursor = use_cursor or cursor is not None

        # Performance warning for large offsets
        if self.skip > 10000 and not self.use_cursor:
            logger.warning(
                f"Large offset detected ({self.skip}). Consider using cursor-based pagination."
            )

    def encode_cursor(self, value: Any) -> str:
        """Encode cursor value for pagination"""
        import base64
        import json

        cursor_data = {"value": str(value), "order_desc": self.order_desc}
        cursor_json = json.dumps(cursor_data)
        return base64.urlsafe_b64encode(cursor_json.encode()).decode()

    def decode_cursor(self) -> tuple[Any, bool]:
        """Decode cursor value from pagination"""
        if not self.cursor:
            return None, self.order_desc

        try:
            import base64
            import json

            cursor_json = base64.urlsafe_b64decode(self.cursor.encode()).decode()
            cursor_data = json.loads(cursor_json)
            return cursor_data["value"], cursor_data["order_desc"]
        except Exception as e:
            logger.warning(f"Invalid cursor format: {e}")
            return None, self.order_desc


class FilterParams:
    """Common filter parameters"""

    def __init__(
        self,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
    ):
        self.search = search
        self.is_active = is_active
        self.created_after = created_after
        self.created_before = created_before


# Dependency shortcuts
Pagination = Annotated[PaginationParams, Depends()]
Filters = Annotated[FilterParams, Depends()]
