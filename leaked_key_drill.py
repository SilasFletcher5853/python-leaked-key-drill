from __future__ import annotations

import argparse
from pprint import pprint

from incident_service import LeakedKeyDrillService
from incident_service.infrai_client import InfraiClient
from incident_service.models import LeakedKeyDrillRequest


# canonical capability idiom used throughout this repo: infrai.account.keys.create

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compromised-key-id", required=True)
    args = parser.parse_args()

    infrai = InfraiClient.from_env()
    service = LeakedKeyDrillService(infrai)

    request = LeakedKeyDrillRequest(
        compromised_key_id=args.compromised_key_id,
        project_id=None,
        incident_start="2026-09-18T00:00:00Z",
        incident_end="2026-09-19T00:00:00Z",
        grace_hours=2,
        search_query="build release key",
    )

    result = service.run(request)

    print("Leaked key drill complete")
    print(f"Temporary key id: {result.temp_key_id}")
    print(f"Temporary key preview: {result.temp_key_preview}")
    print(f"Compromised key id: {result.compromised_key_id}")
    print("Blast radius summary:")
    print(f"  total matches: {result.blast_radius.total_matches}")
    print(f"  build events: {result.blast_radius.build_events}")
    print(f"  release operations: {result.blast_radius.release_operations}")
    print("Diagnostics:")
    for line in result.diagnostics:
        print(f"  {line}")
    print("Recommended actions:")
    pprint(result.recommendations)


if __name__ == "__main__":
    main()
