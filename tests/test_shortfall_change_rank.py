from pathlib import Path

import duckdb


def test_rank_is_directional_deterministic_and_null_for_zero_or_unknown():
    sql = Path('models/marts/rpt_loan_shortfall_change_ranked.sql').read_text()
    sql = sql.replace("{{ ref('rpt_loan_monthly_shortfall_contribution') }}", 'fixture')
    with duckdb.connect() as con:
        con.execute("""
            create table fixture as select date '2025-02-28' snapshot_date,
                id account_id, known has_previous_month,
                delta scheduled_principal_shortfall_change
            from (values ('B',true,5),('A',true,5),('C',true,-9),
                ('D',true,-3),('E',true,0),('F',false,null)) t(id,known,delta);
        """)
        rows = con.execute('select account_id, change_direction, direction_rank from ('
                           + sql + ') order by account_id').fetchall()
    assert rows == [('A', 'Increase', 1), ('B', 'Increase', 2),
                    ('C', 'Decrease', 1), ('D', 'Decrease', 2),
                    ('E', 'Unchanged', None), ('F', 'No comparator', None)]
