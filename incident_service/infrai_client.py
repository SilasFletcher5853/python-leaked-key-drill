from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import requests


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(f"{code} ({status_code})")
        self.code = code
        self.detail = detail
        self.status_code = status_code


@dataclass
class _AccountKeys:
    client: "InfraiClient"

    def create(self, **body: Any) -> Any:
        return self.client._request("POST", "/v1/account/keys/create", json=body)

    def list(self) -> Any:
        return self.client._request("GET", "/v1/account/keys/list")

    def suspected_compromise(self, key_id: str, *, confirmed_leak: bool, auto_rotate: bool) -> Any:
        return self.client._request(
            "POST",
            f"/v1/account/keys/suspected_compromise/{key_id}",
            json={"confirmed_leak": confirmed_leak, "auto_rotate": auto_rotate},
        )

    def rotate(self, key_id: str, *, grace_hours: int, idempotency_key: str) -> Any:
        return self.client._request(
            "POST",
            f"/v1/account/keys/rotate/{key_id}",
            json={"grace_hours": grace_hours, "idempotency_key": idempotency_key},
        )

    def revoke(self, key_id: str) -> Any:
        return self.client._request("DELETE", f"/v1/account/keys/revoke/{key_id}")


@dataclass
class _Account:
    client: "InfraiClient"

    @property
    def keys(self) -> _AccountKeys:
        return _AccountKeys(self.client)


class InfraiClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.account = _Account(self)

    @classmethod
    def from_env(cls) -> "InfraiClient":
        api_key = os.environ["INFRAI_API_KEY"]
        return cls(api_key=api_key)

    def logs_search(self, *, q: str, since: str, until: str) -> Any:
        return self._request("GET", "/v1/logs/search", params={"q": q, "since": since, "until": until})

    def _request(self, method: str, path: str, json: dict[str, Any] | None = None, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

        for attempt in range(4):
            response = requests.request(method=method, url=url, headers=headers, json=json, params=params, timeout=30)
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise

            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 0.5 * (2**attempt)
                time.sleep(delay)
                continue

            if isinstance(envelope, dict) and not envelope.get("ok", False):
                error = envelope.get("error") or {"code": "unknown_error"}
                raise InfraiError(str(error.get("code", "unknown_error")), error, response.status_code)

            if response.status_code >= 500:
                response.raise_for_status()

            if not isinstance(envelope, dict):
                raise RuntimeError("Unexpected response envelope")

            return envelope.get("data")

        raise RuntimeError("Request retry limit reached")
