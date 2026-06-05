"""Abstract base class for HTTP clients."""

from abc import ABC, abstractmethod
from typing import Any


class BaseHTTPClient(ABC):
    """Contract for HTTP client implementations."""

    @abstractmethod
    async def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a GET request.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response as dictionary
        """
        ...

    @abstractmethod
    async def post(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a POST request.

        Args:
            endpoint: API endpoint path
            data: Request body

        Returns:
            JSON response as dictionary
        """
        ...

    @abstractmethod
    async def put(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a PUT request.

        Args:
            endpoint: API endpoint path
            data: Request body

        Returns:
            JSON response as dictionary
        """
        ...

    @abstractmethod
    async def delete(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a DELETE request.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response as dictionary
        """
        ...

    @abstractmethod
    async def connect(self) -> None:
        """Initialize the HTTP session."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the HTTP session."""
        ...
