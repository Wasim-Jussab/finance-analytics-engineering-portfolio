from pathlib import Path

import duckdb


def test_current_assignment_action_boundaries():
    model = Path(__file__).parents[1] / "models/marts/rpt_loan_current_assignment_action.sql"
    sql = model.read_text()
    for name in (
        "rpt_loan_delinquency_case_status",
        "fct_loan_case_assignment",
        "fct_loan_collection_action",
    ):
        sql = sql.replace("{{ ref('" + name + "') }}", name)
    with duckdb.connect() as connection:
        connection.execute("""
            create table rpt_loan_delinquency_case_status as
            select account_id, date '2025-12-31' as as_of_date,
                case when account_id = 'unassigned' then null else account_id end
                    as current_assignment_id,
                case when account_id = 'unassigned' then null else 'Team A' end
                    as current_assigned_team
            from (values ('unassigned'), ('before'), ('equal'), ('later'), ('future'))
                as accounts(account_id);
            create table fct_loan_case_assignment as
            select current_assignment_id as assignment_id,
                timestamp '2025-12-01 09:00:00' as assigned_at
            from rpt_loan_delinquency_case_status where current_assignment_id is not null;
            create table fct_loan_collection_action (
                account_id varchar, action_at timestamp
            );
            insert into fct_loan_collection_action values
                ('unassigned', '2025-12-02 09:00:00'),
                ('before', '2025-11-30 09:00:00'),
                ('equal', '2025-12-01 09:00:00'),
                ('later', '2025-12-02 09:00:00'),
                ('later', '2025-12-03 09:00:00'),
                ('future', '2026-01-01 09:00:00');
        """)
        cursor = connection.execute(sql)
        columns = [column[0] for column in cursor.description]
        result = {row[0]: dict(zip(columns, row, strict=True)) for row in cursor.fetchall()}
        assert result["unassigned"]["assignment_action_state"] == "Unassigned"
        for account in ("before", "future"):
            assert result[account]["assignment_action_state"] == (
                "No action since current assignment"
            )
        assert result["equal"]["minutes_to_first_observed_action"] == 0
        assert result["later"]["minutes_to_first_observed_action"] == 1440
