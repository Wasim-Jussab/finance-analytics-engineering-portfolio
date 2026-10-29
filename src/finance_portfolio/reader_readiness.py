"""Fail-closed readiness probe for direct consumers of the completed database."""

import argparse
import json
from pathlib import Path

import duckdb


def probe_database(database: Path) -> dict:
    """Read the original database only; never repair it or bypass its recovery file."""
    result = {
        "status": "unavailable",
        "reason": None,
        "reader_opened": False,
        "wal_present": None,
        "population_counts": None,
        "error_type": None,
    }
    try:
        result["wal_present"] = Path(f"{database}.wal").exists()
        exists = database.is_file()
    except OSError as error:
        return {**result, "reason": "filesystem_access_error", "error_type": type(error).__name__}
    if not exists:
        return {**result, "reason": "database_missing"}
    try:
        with duckdb.connect(str(database), read_only=True) as connection:
            result["reader_opened"] = True
            queries = {
                "activity_accounts": "select count(*) from mart.rpt_loan_case_activity_summary",
                "assignment_accounts": (
                    "select count(*) from mart.rpt_loan_current_assignment_action"
                ),
                "activity_aggregate_accounts": (
                    "select coalesce(sum(account_count), 0) from mart.agg_loan_case_team_coverage"
                ),
                "assignment_aggregate_accounts": (
                    "select coalesce(sum(queue_account_count), 0) "
                    "from mart.agg_loan_assignment_action_coverage"
                ),
            }
            counts = {name: connection.execute(sql).fetchone()[0] for name, sql in queries.items()}
    except duckdb.Error as error:
        reason = (
            "wal_replay_error"
            if "Failure while replaying WAL file" in str(error)
            else "database_read_error"
        )
        return {**result, "reason": reason, "error_type": type(error).__name__}
    consistent = len(set(counts.values())) == 1
    return {
        **result,
        "status": "ready" if consistent else "inconsistent",
        "reason": None if consistent else "case_population_mismatch",
        "population_counts": counts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("data/finance.duckdb"))
    report = probe_database(parser.parse_args().database)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["status"] == "ready" else 1)


if __name__ == "__main__":
    main()
