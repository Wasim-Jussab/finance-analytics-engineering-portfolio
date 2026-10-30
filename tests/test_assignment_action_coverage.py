from pathlib import Path

import duckdb


def test_assigned_denominator_and_empty_unassigned_rate():
    model = Path(__file__).parents[1] / "models/marts/agg_loan_assignment_action_coverage.sql"
    sql = model.read_text().replace(
        "{{ ref('rpt_loan_current_assignment_action') }}", "rpt_loan_current_assignment_action"
    )
    with duckdb.connect() as connection:
        connection.execute("""
            create table rpt_loan_current_assignment_action as
            select date '2025-12-31' as as_of_date, *
            from (values
                ('Team A', 'a1', timestamp '2025-12-02 09:00:00'),
                ('Team A', 'a2', null),
                (null, null, null)
            ) as cases(current_assigned_team, current_assignment_id,
                first_action_after_assignment_at)
        """)
        result = {row[1]: row for row in connection.execute(sql).fetchall()}
        assert result["Team A"][2:] == (2, 2, 0, 1, 1, 0.5)
        assert result[None][2:] == (1, 0, 1, 0, 0, None)
