from pathlib import Path

import duckdb


def test_cumulative_share_uses_gross_direction_not_net_or_other_months():
    sql = Path('models/marts/rpt_loan_shortfall_change_ranked.sql').read_text()
    sql = sql.replace("{{ ref('rpt_loan_monthly_shortfall_contribution') }}", 'fixture')
    with duckdb.connect() as con:
        con.execute("""
            create table fixture as select date '2025-02-28' snapshot_date,
                id account_id, known has_previous_month,
                delta scheduled_principal_shortfall_change
            from (values ('B',true,5),('A',true,5),('C',true,-9),
                ('D',true,-3),('E',true,0),('F',false,null)) t(id,known,delta);
            insert into fixture values (date '2025-03-31','G',true,20);
        """)
        rows = con.execute(
            'select account_id, direction_gross_change_amount, cumulative_gross_change_amount, '
            'cumulative_gross_change_share from (' + sql + ') order by account_id'
        ).fetchall()
    assert rows == [('A', 10, 5, .5), ('B', 10, 10, 1),
                    ('C', 12, 9, .75), ('D', 12, 12, 1),
                    ('E', None, None, None), ('F', None, None, None), ('G', 20, 20, 1)]
