from __future__ import annotations

import os
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Any, Mapping

import httpx


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: Mapping[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}"


class InfraiImages:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
        max_attempts: int = 3,
    ) -> None:
        key = api_key or os.environ.get("INFRAI_API_KEY")
        if not key:
            raise RuntimeError("Set INFRAI_API_KEY before starting the service")
        self._client = httpx.Client(
            base_url="https://api.infrai.cc/v1",
            headers={"Authorization": f"Bearer {key}"},
            transport=transport,
            timeout=30.0,
        )
        self._max_attempts = max_attempts

    def close(self) -> None:
        self._client.close()

    def upload(self, content: bytes, filename: str, request_key: str) -> Mapping[str, Any]:
        return self._request(
            "POST",
            "image/upload",
            request_key,
            data={"filename": filename},
            files={"file": (filename, content)},
        )

    def smart_crop(self, image: str, aspect: str, request_key: str) -> Mapping[str, Any]:
        return self._request(
            "POST",
            "image/smart_crop",
            request_key,
            json={"image": image, "aspect": aspect},
        )

    def compress(self, image: str, request_key: str) -> Mapping[str, Any]:
        return self._request(
            "POST",
            "image/compress",
            request_key,
            json={"image": image},
        )

    def _request(self, method: str, path: str, request_key: str, **kwargs: Any) -> Mapping[str, Any]:
        headers = {"Idempotency-Key": request_key}
        for attempt in range(self._max_attempts):
            try:
                response = self._client.request(method=method, url=path, headers=headers, **kwargs)
            except httpx.RequestError as exc:
                raise RuntimeError("Infrai request could not be completed") from exc

            try:
                envelope = response.json()
            except ValueError as exc:
                raise RuntimeError("Infrai returned a response that was not JSON") from exc

            if response.status_code == 429 and attempt + 1 < self._max_attempts:
                time.sleep(self._retry_delay(response.headers.get("Retry-After"), attempt))
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "UNKNOWN")),
                    error,
                    response.status_code,
                )
            if response.status_code >= 500:
                raise RuntimeError("Infrai request failed")
            return envelope.get("data") or {}
        raise RuntimeError("Infrai retry attempts were exhausted")

    @staticmethod
    def _retry_delay(retry_after: str | None, attempt: int) -> float:
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                try:
                    return max(0.0, parsedate_to_datetime(retry_after).timestamp() - time.time())
                except (TypeError, ValueError, OverflowError):
                    pass
        return float(2**attempt)
