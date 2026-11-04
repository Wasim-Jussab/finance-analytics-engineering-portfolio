"""Inspect a local pipeline lock and matching run evidence without changing either."""

import argparse
import json
import re
from pathlib import Path


def inspect_lock(lock: Path, runs: Path) -> dict:
    result = {
        "status": "unresolved",
        "run_id": None,
        "recorded_process_id": None,
        "matching_run_status": None,
        "safe_to_remove": False,
    }
    try:
        payload = json.loads(lock.read_text())
    except FileNotFoundError:
        return {**result, "status": "unlocked"}
    except (ValueError, OSError):
        return result
    if not isinstance(payload, dict):
        return result
    run_id, pid = payload.get("run_id"), payload.get("process_id")
    if (
        not isinstance(run_id, str)
        or re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", run_id)
        is None
        or type(pid) is not int
        or pid <= 0
    ):
        return result
    result.update(run_id=run_id, recorded_process_id=pid)
    try:
        evidence = json.loads((runs / f"{run_id}.json").read_text())
    except (OSError, ValueError):
        return result
    if not isinstance(evidence, dict):
        return result
    if (
        evidence.get("run_id") == run_id
        and isinstance(payload.get("started_at"), str)
        and evidence.get("started_at") == payload["started_at"]
        and isinstance(evidence.get("finished_at"), str)
        and evidence.get("status") in ("succeeded", "failed")
    ):
        result.update(status="retained_completed_run", matching_run_status=evidence["status"])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=Path("reports/pipeline.lock"))
    parser.add_argument("--runs", type=Path, default=Path("reports/runs"))
    args = parser.parse_args()
    result = inspect_lock(args.lock, args.runs)
    print(json.dumps(result, indent=2))
    # A completed report is written before lock release, so it cannot prove staleness.
    raise SystemExit(0 if result["status"] == "unlocked" else 1)


if __name__ == "__main__":
    main()
