from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager

from fastapi import Request, Response


class UpstreamUnavailable(Exception):
    """Raised when a transport cannot complete an upstream request."""


class UpstreamTransport(ABC):
    """Plugin contract for sending admitted requests to an upstream service."""

    @abstractmethod
    def lifecycle(self) -> AbstractAsyncContextManager[None]:
        """Own transport resources for the lifetime of the application."""

    @abstractmethod
    async def forward(self, request: Request) -> Response:
        """Forward one incoming request and return the upstream response."""
