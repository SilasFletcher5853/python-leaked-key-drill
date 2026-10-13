from __future__ import annotations

from .models import BlastRadiusSummary, DeveloperDiagnostics


def summarize_logs(payload: object) -> BlastRadiusSummary:
    items = payload if isinstance(payload, list) else []
    build_events = 0
    release_operations = 0

    for item in items:
        text = str(item).lower()
        if "build" in text:
            build_events += 1
        if "release" in text:
            release_operations += 1

    return BlastRadiusSummary(
        total_matches=len(items),
        build_events=build_events,
        release_operations=release_operations,
        raw_items=items,
    )


def make_diagnostics(summary: BlastRadiusSummary) -> DeveloperDiagnostics:
    if summary.release_operations > 0 or summary.build_events >= 2:
        severity = "high"
    elif summary.total_matches > 0:
        severity = "medium"
    else:
        severity = "low"

    lines = [
        f"Observed {summary.total_matches} matching log records in the incident window.",
        f"Build events mentioning the key path: {summary.build_events}.",
        f"Release operations mentioning the key path: {summary.release_operations}.",
    ]

    recommendations = ["Create a clean replacement key for build and release automation."]
    if severity == "high":
        recommendations.append("Rotate rollout credentials now.")
        recommendations.append("Review recent build artifacts and deployment releases.")
    elif severity == "medium":
        recommendations.append("Confirm ownership of the matching jobs before ending the drill.")
    else:
        recommendations.append("Record the drill result and keep the old key disabled.")

    return DeveloperDiagnostics(
        severity=severity,
        lines=lines,
        recommendations=recommendations,
    )
