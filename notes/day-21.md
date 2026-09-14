# Day 21 — keeping plan changes instead of overwriting them

Today I added the first SCD Type 2 history to the project.

The subscription plan table is small, but it is a useful place to learn the pattern. If a plan amount or billing frequency changes, replacing the row would make it impossible to explain what the pipeline previously saw. The dbt snapshot now closes the old version and creates a new current version.

I used the plan ID as the stable key and the check strategy for product code, billing frequency and amount. I deliberately left the load ID and ingestion timestamp out of the checked columns. Those fields change with a load, not with the plan definition, and including them would create a false version every time the same files were reloaded.

I also added controls for:

- one current version per plan;
- no invalid or overlapping validity windows;
- exact agreement between the current snapshot rows and the current source;
- unique dbt version identifiers.

The repeatable change check works on a temporary copy of the database. It adds £0.01 to one synthetic monthly plan, runs the snapshot again and expects five versions in total: four current rows and one closed row. The normal local database and committed synthetic inputs are not changed.

The important limitation is that `dbt_valid_from` means “when this pipeline observed the change”. It is not a contractual effective date. I should not use it to claim historical pricing before the first snapshot run, and I have kept the existing reporting marts on the current plan definitions for now.
