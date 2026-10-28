from pathlib import Path

import duckdb


def test_assignment_window_flows_into_team_coverage_without_losing_unassigned_cases():
    models = Path(__file__).parents[1] / "models/marts"
    names = ("rpt_loan_current_assignment_action", "agg_loan_assignment_action_coverage")
    references = (
        "rpt_loan_delinquency_case_status",
        "fct_loan_case_assignment",
        "fct_loan_collection_action",
        "rpt_loan_current_assignment_action",
    )
    with duckdb.connect() as connection:
        connection.execute("""
            create table rpt_loan_delinquency_case_status as
            select account_id, date '2025-12-31' as as_of_date,
                assignment_id as current_assignment_id, team as current_assigned_team
            from (values ('reassigned', 'new', 'Team A'), ('observed', 'other', 'Team A'),
                ('unassigned', null, null)) as cases(account_id, assignment_id, team);
            create table fct_loan_case_assignment as
            select * from (values
                ('old', timestamp '2025-11-01 09:00:00'),
                ('new', timestamp '2025-12-01 09:00:00'),
                ('other', timestamp '2025-12-01 09:00:00')
            ) as assignments(assignment_id, assigned_at);
            create table fct_loan_collection_action as
            select * from (values
                ('reassigned', timestamp '2025-11-02 09:00:00'),
                ('reassigned', timestamp '2026-01-01 09:00:00'),
                ('observed', timestamp '2025-12-01 09:00:00'),
                ('observed', timestamp '2025-12-02 09:00:00'),
                ('unassigned', timestamp '2025-12-02 09:00:00')
            ) as actions(account_id, action_at)
        """)
        for name in names:
            sql = (models / f"{name}.sql").read_text()
            for ref in references:
                sql = sql.replace("{{ ref('" + ref + "') }}", ref)
            connection.execute(f"create table {name} as {sql}")
        accounts = connection.execute(
            "select account_id, minutes_to_first_observed_action, assignment_action_state "
            "from rpt_loan_current_assignment_action order by account_id"
        ).fetchall()
        assert accounts == [
            ("observed", 0, "Action observed since current assignment"),
            ("reassigned", None, "No action since current assignment"),
            ("unassigned", None, "Unassigned"),
        ]
        rows = connection.execute(
            "select current_assigned_team, queue_account_count, assigned_account_count, "
            "unassigned_account_count, assigned_accounts_with_action, "
            "assigned_accounts_without_action, assigned_action_coverage_rate "
            "from agg_loan_assignment_action_coverage order by current_assigned_team nulls last"
        ).fetchall()
        assert rows == [("Team A", 2, 2, 0, 1, 1, 0.5), (None, 1, 0, 1, 0, 0, None)]
