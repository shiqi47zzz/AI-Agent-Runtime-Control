import os
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class Settings:
    upstream_url: str
    max_in_flight: int = 20
    upstream_timeout_seconds: float = 30.0

    @classmethod
    def from_env(cls) -> "Settings":
        upstream_url = os.getenv("UPSTREAM_URL", "http://localhost:9000")
        parsed = urlparse(upstream_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("UPSTREAM_URL must be an absolute HTTP(S) URL")

        max_in_flight = int(os.getenv("MAX_IN_FLIGHT", "20"))
        timeout = float(os.getenv("UPSTREAM_TIMEOUT_SECONDS", "30"))
        if max_in_flight < 1:
            raise ValueError("MAX_IN_FLIGHT must be positive")
        if timeout <= 0:
            raise ValueError("UPSTREAM_TIMEOUT_SECONDS must be positive")

        return cls(upstream_url.rstrip("/"), max_in_flight, timeout)
