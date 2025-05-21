from dataclasses import dataclass
from fastapi import HTTPException
from limits import RateLimitItemPerMinute, RateLimitItemPerHour, RateLimitItemPerDay
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter
from typing import Dict, TypeVar, Callable

T = TypeVar("T")


@dataclass
class RateLimitConfig:
    qpm: int  # Queries per minute
    qph: int  # Queries per hour
    qpd: int  # Queries per day


# Rate limit configurations
RATE_LIMITS: Dict[str, RateLimitConfig] = {
    "search": RateLimitConfig(qpm=600, qph=10000, qpd=100000),
    "chat": RateLimitConfig(qpm=300, qph=1000, qpd=5000),
    "think": RateLimitConfig(qpm=300, qph=1000, qpd=5000),
    "research": RateLimitConfig(qpm=300, qph=1000, qpd=5000),
    "feedback": RateLimitConfig(qpm=600, qph=10000, qpd=100000),
}


class RateLimiter:
    def __init__(self):
        self.storage = MemoryStorage()
        self.rate_limiter = MovingWindowRateLimiter(self.storage)
        self._init_rate_limit_items()

    def _init_rate_limit_items(self):
        self.rate_limit_items = {}
        for endpoint, config in RATE_LIMITS.items():
            self.rate_limit_items[endpoint] = {
                "qpm": RateLimitItemPerMinute(config.qpm, 1),
                "qph": RateLimitItemPerHour(config.qph, 1),
                "qpd": RateLimitItemPerDay(config.qpd, 1),
            }

    def _check_rate_limit(self, endpoint: str) -> None:
        items = self.rate_limit_items[endpoint]
        if not all(self.rate_limiter.hit(item, endpoint) for item in items.values()):
            raise HTTPException(status_code=429, detail="Too Many Requests")

    def __getattr__(self, name: str) -> Callable[[], None]:
        if name.startswith("hit_") and name[4:] in RATE_LIMITS:
            endpoint = name[4:]
            return lambda: self._check_rate_limit(endpoint)
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )


# Create a singleton instance
rate_limiter = RateLimiter()
