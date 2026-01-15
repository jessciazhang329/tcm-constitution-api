"""
安全与鉴权相关逻辑
"""

from __future__ import annotations

import hashlib
import os
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, List, Optional


@dataclass
class APIError(Exception):
    code: str
    message: str
    status_code: int


class UnauthorizedError(APIError):
    def __init__(self, message: str = "未授权"):
        super().__init__(code="UNAUTHORIZED", message=message, status_code=401)


class RateLimitError(APIError):
    def __init__(self, message: str = "请求过于频繁"):
        super().__init__(code="RATE_LIMITED", message=message, status_code=429)


class PayloadTooLargeError(APIError):
    def __init__(self, message: str = "请求体过大"):
        super().__init__(code="PAYLOAD_TOO_LARGE", message=message, status_code=413)


def get_api_keys() -> List[str]:
    raw = os.getenv("API_KEYS", "")
    return [k.strip() for k in raw.split(",") if k.strip()]


def get_rate_limit_per_minute() -> int:
    raw = os.getenv("RATE_LIMIT_PER_MIN")
    if raw is None or raw == "":
        raw = os.getenv("RATE_LIMIT_PER_MINUTE", "60")
    try:
        return max(1, int(raw))
    except ValueError:
        return 60


def get_allowed_origins() -> List[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "").strip()
    if not raw:
        return []
    return [o.strip() for o in raw.split(",") if o.strip()]


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:12]


class RateLimiter:
    def __init__(self, limit_per_minute: int):
        self.limit_per_minute = limit_per_minute
        self._store: Dict[str, Deque[float]] = {}

    def check(self, api_key: str) -> None:
        now = time.time()
        window_start = now - 60
        bucket = self._store.setdefault(api_key, deque())

        while bucket and bucket[0] < window_start:
            bucket.popleft()

        if len(bucket) >= self.limit_per_minute:
            raise RateLimitError(
                message=f"超过每分钟 {self.limit_per_minute} 次的限制"
            )

        bucket.append(now)


def parse_bearer_token(auth_header: Optional[str]) -> Optional[str]:
    if not auth_header:
        return None
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip()


def error_payload(code: str, message: str, trace_id: str) -> Dict[str, Dict[str, str]]:
    return {"error": {"code": code, "message": message, "trace_id": trace_id}}
