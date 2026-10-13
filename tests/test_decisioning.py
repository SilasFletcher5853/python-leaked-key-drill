from incident_service.decisioning import make_diagnostics
from incident_service.models import BlastRadiusSummary


def test_high_severity_when_builds_and_release_show_up() -> None:
    summary = BlastRadiusSummary(
        total_matches=3,
        build_events=2,
        release_operations=1,
        raw_items=[
            {"event": "build.started"},
            {"event": "build.finished"},
            {"event": "release.promoted"},
        ],
    )

    diagnostics = make_diagnostics(summary)

    assert diagnostics.severity == "high"
    assert "Rotate rollout credentials now." in diagnostics.recommendations
