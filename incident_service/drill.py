from __future__ import annotations

import uuid
from typing import Any

from .decisioning import make_diagnostics, summarize_logs
from .models import LeakedKeyDrillRequest, LeakedKeyDrillResult


class LeakedKeyDrillService:
    def __init__(self, infrai: Any) -> None:
        self.infrai = infrai

    def run(self, request: LeakedKeyDrillRequest) -> LeakedKeyDrillResult:
        self.infrai.account.keys.list()

        self.infrai.account.keys.suspected_compromise(
            request.compromised_key_id,
            confirmed_leak=True,
            auto_rotate=False,
        )

        temp_key = self.infrai.account.keys.create(
            project_id=request.project_id,
            name="incident-drill-temporary-release-key",
            scopes=["logs.search"],
            idempotency_key=f"create-{uuid.uuid4()}",
        )

        temp_key_id = str(temp_key.get("key_id", ""))
        temp_key_value = str(temp_key.get("key", ""))
        temp_key_preview = temp_key_value[:8] + "..." if temp_key_value else "hidden"

        self.infrai.account.keys.rotate(
            temp_key_id,
            grace_hours=request.grace_hours,
            idempotency_key=f"rotate-{uuid.uuid4()}",
        )

        logs = self.infrai.logs_search(
            q=request.search_query,
            since=request.incident_start,
            until=request.incident_end,
        )
        summary = summarize_logs(logs)
        diagnostics = make_diagnostics(summary)

        self.infrai.account.keys.revoke(temp_key_id)

        return LeakedKeyDrillResult(
            compromised_key_id=request.compromised_key_id,
            temp_key_id=temp_key_id,
            temp_key_preview=temp_key_preview,
            blast_radius=summary,
            diagnostics=[f"[{diagnostics.severity}] {line}" for line in diagnostics.lines],
            recommendations=diagnostics.recommendations,
        )
