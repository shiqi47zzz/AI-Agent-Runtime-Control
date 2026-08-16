from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager

from fastapi import Request


class CapacityRejected(Exception):
    """Raised when a control refuses an upstream call."""


class AdmissionControl(ABC):
    """Plugin contract for controls that guard upstream capacity."""

    @abstractmethod
    def admission(self, request: Request) -> AbstractAsyncContextManager[None]:
        """Return a context manager covering the admitted upstream call."""
