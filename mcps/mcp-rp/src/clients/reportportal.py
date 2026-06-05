"""Async ReportPortal API client with OAuth support."""

import asyncio
import ssl
from typing import Any

import aiohttp
from aiohttp import BasicAuth, ClientTimeout

from src.clients.base import BaseHTTPClient
from src.utils.logging import get_logger
from src.utils.retry import RetryConfig, async_retry

logger = get_logger(__name__)


class AuthenticationError(Exception):
    """Raised when authentication fails."""


class OAuthTokenManager:
    """Manages OAuth token acquisition and refresh for ReportPortal 5.x."""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        verify_ssl: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self._access_token: str | None = None

    async def get_token(self, session: aiohttp.ClientSession) -> str:
        """Get OAuth access token, fetching new one if needed."""
        if not self._access_token:
            await self._fetch_token(session)
        return self._access_token

    async def _fetch_token(self, session: aiohttp.ClientSession) -> None:
        """Fetch new OAuth token from ReportPortal."""
        oauth_url = f"{self.base_url}/uat/sso/oauth/token"
        auth = BasicAuth("ui", "uiman")
        data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
        }

        logger.debug("fetching_oauth_token", url=oauth_url, username=self.username)

        try:
            async with session.post(oauth_url, data=data, auth=auth) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self._access_token = token_data.get("access_token")
                    logger.info("oauth_token_obtained")
                else:
                    error_text = await response.text()
                    logger.error(
                        "oauth_token_failed",
                        status=response.status,
                        error=error_text[:500],
                    )
                    raise AuthenticationError(
                        f"Failed to get OAuth token: {response.status} - {error_text[:200]}"
                    )
        except aiohttp.ClientError as e:
            logger.error("oauth_request_failed", error=str(e))
            raise AuthenticationError(f"OAuth request failed: {e}") from e

    def invalidate(self) -> None:
        """Invalidate current token to force refresh."""
        self._access_token = None


class ReportPortalClient(BaseHTTPClient):
    """Async client for ReportPortal 5.x API.

    Supports both Bearer token and OAuth (username/password) authentication.
    Includes rate limiting via semaphore and automatic retries with backoff.

    Args:
        url: ReportPortal server URL
        project: Project name
        token: API bearer token (optional if username/password provided)
        username: ReportPortal username for OAuth
        password: ReportPortal password for OAuth
        verify_ssl: Whether to verify SSL certificates
        timeout: Request timeout in seconds
        max_concurrent: Maximum concurrent requests
        retry_config: Retry configuration for failed requests
    """

    def __init__(
        self,
        url: str,
        project: str,
        token: str | None = None,
        username: str | None = None,
        password: str | None = None,
        verify_ssl: bool = True,
        timeout: float = 30.0,
        max_concurrent: int = 5,
        retry_config: RetryConfig | None = None,
    ):
        self.url = url.rstrip("/")
        self.project = project
        self.token = token
        self.verify_ssl = verify_ssl
        self.timeout = ClientTimeout(total=timeout)
        self.retry_config = retry_config or RetryConfig()
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._session: aiohttp.ClientSession | None = None
        self._oauth_manager: OAuthTokenManager | None = None

        if not token and not (username and password):
            raise ValueError(
                "Either 'token' or both 'username' and 'password' must be provided"
            )

        if username and password and not token:
            self._oauth_manager = OAuthTokenManager(
                base_url=self.url,
                username=username,
                password=password,
                verify_ssl=verify_ssl,
            )

    @property
    def project_base_url(self) -> str:
        """Base API URL scoped to the configured project."""
        return f"{self.url}/api/v1/{self.project}"

    @property
    def global_base_url(self) -> str:
        """Base API URL for global (non-project) endpoints."""
        return f"{self.url}/api/v1"

    def _get_base_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _get_auth_headers(self) -> dict[str, str]:
        headers = self._get_base_headers()
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        elif self._oauth_manager and self._session:
            token = await self._oauth_manager.get_token(self._session)
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _ensure_session(self) -> aiohttp.ClientSession:
        if not self._session:
            raise RuntimeError(
                "Client not initialized. Call connect() first."
            )
        return self._session

    async def connect(self) -> None:
        """Initialize HTTP session and authenticate if using OAuth."""
        if not self.verify_ssl:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ssl_context)
        else:
            connector = aiohttp.TCPConnector()

        self._session = aiohttp.ClientSession(
            timeout=self.timeout,
            connector=connector,
        )

        if self._oauth_manager:
            await self._oauth_manager.get_token(self._session)
            logger.info("oauth_authenticated")

    async def disconnect(self) -> None:
        """Close HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None

    @async_retry()
    async def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        session = self._ensure_session()
        url = self._resolve_url(endpoint)
        headers = await self._get_auth_headers()

        async with self._semaphore:
            logger.debug("api_request", method="GET", url=url, params=params)
            async with session.get(url, params=params, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                logger.debug("api_response", status=response.status, url=url)
                return data

    @async_retry()
    async def post(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        session = self._ensure_session()
        url = self._resolve_url(endpoint)
        headers = await self._get_auth_headers()

        async with self._semaphore:
            logger.debug("api_request", method="POST", url=url)
            async with session.post(url, json=data, headers=headers) as response:
                response.raise_for_status()
                result = await response.json()
                logger.debug("api_response", status=response.status, url=url)
                return result

    @async_retry()
    async def put(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        session = self._ensure_session()
        url = self._resolve_url(endpoint)
        headers = await self._get_auth_headers()

        async with self._semaphore:
            logger.debug("api_request", method="PUT", url=url)
            async with session.put(url, json=data, headers=headers) as response:
                response.raise_for_status()
                result = await response.json()
                logger.debug("api_response", status=response.status, url=url)
                return result

    @async_retry()
    async def delete(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        session = self._ensure_session()
        url = self._resolve_url(endpoint)
        headers = await self._get_auth_headers()

        async with self._semaphore:
            logger.debug("api_request", method="DELETE", url=url)
            async with session.delete(url, params=params, headers=headers) as response:
                response.raise_for_status()
                if response.content_type == "application/json":
                    result = await response.json()
                else:
                    result = {"message": await response.text()}
                logger.debug("api_response", status=response.status, url=url)
                return result

    def _resolve_url(self, endpoint: str) -> str:
        """Resolve a full URL from an endpoint path.

        Endpoints starting with '/v1/' are treated as absolute API paths.
        Others are scoped to the configured project.
        """
        endpoint = endpoint.lstrip("/")
        if endpoint.startswith("v1/"):
            return f"{self.url}/api/{endpoint}"
        return f"{self.project_base_url}/{endpoint}"
