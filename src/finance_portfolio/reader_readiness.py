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
        "account_checks": None,
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
            # All checks observe one consistent read transaction, not successive loads.
            connection.execute("begin transaction")
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
            checks = {}
            for label, table in (
                ("activity", "rpt_loan_case_activity_summary"),
                ("assignment", "rpt_loan_current_assignment_action"),
            ):
                invalid, duplicates = connection.execute(f"""
                    select count(*) filter (where account_id is null or as_of_date is null),
                        count(account_id) - count(distinct account_id)
                    from mart.{table}
                """).fetchone()
                checks[f"{label}_null_key_or_date_rows"] = invalid
                checks[f"{label}_duplicate_account_rows"] = duplicates
            checks["account_date_symmetric_difference"] = connection.execute("""
                with activity_only as (
                    select account_id, as_of_date from mart.rpt_loan_case_activity_summary
                    except
                    select account_id, as_of_date from mart.rpt_loan_current_assignment_action
                ), assignment_only as (
                    select account_id, as_of_date from mart.rpt_loan_current_assignment_action
                    except
                    select account_id, as_of_date from mart.rpt_loan_case_activity_summary
                )
                select (select count(*) from activity_only)
                     + (select count(*) from assignment_only)
            """).fetchone()[0]
            connection.execute("commit")
    except duckdb.Error as error:
        reason = (
            "wal_replay_error"
            if "Failure while replaying WAL file" in str(error)
            else "database_read_error"
        )
        return {**result, "reason": reason, "error_type": type(error).__name__}
    counts_match = len(set(counts.values())) == 1
    keys_match = all(value == 0 for value in checks.values())
    consistent = counts_match and keys_match
    return {
        **result,
        "status": "ready" if consistent else "inconsistent",
        "reason": (
            "case_population_mismatch" if not counts_match
            else "case_account_grain_mismatch" if not keys_match else None
        ),
        "population_counts": counts,
        "account_checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("data/finance.duckdb"))
    report = probe_database(parser.parse_args().database)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["status"] == "ready" else 1)


if __name__ == "__main__":
    main()
