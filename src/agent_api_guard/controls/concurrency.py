import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Request

from .base import AdmissionControl, CapacityRejected


class ConcurrencyLimit(AdmissionControl):
    def __init__(self, limit: int) -> None:
        if limit < 1:
            raise ValueError("limit must be positive")
        self._limit = limit
        self._in_flight = 0
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def admission(self, request: Request) -> AsyncIterator[None]:
        del request  # Reserved for tenant-, route-, or agent-aware policies.
        async with self._lock:
            if self._in_flight >= self._limit:
                raise CapacityRejected
            self._in_flight += 1

        try:
            yield
        finally:
            async with self._lock:
                self._in_flight -= 1
