
# Initial architecture notes

## Why I am starting locally

I do not want the first step to be creating cloud resources that I barely use or could accidentally leave running. I can learn the modelling, testing and pipeline structure locally first, then document how the same design would map to S3, Glue and Redshift.

The first version is therefore deliberately simple:

~~~mermaid
flowchart TD
    A["Generated source data"] --> B["Python load and checks"]
    B --> C["Local raw tables"]
    C --> D["SQL and dbt models"]
    D --> E["Reconciliation and quality checks"]
    E --> F["Reporting outputs"]
~~~

## What each part is for

| Part | Why it is here |
|---|---|
| Generated source data | Gives me realistic edge cases without using work data |
| Python load | Lets me practise repeatable ingestion and validation |
| Raw tables | Keeps the input separate from business logic |
| SQL and dbt models | Gives the project a clear transformation layer |
| Quality checks | Proves whether the output is complete and explainable |
| Reporting outputs | Connects the engineering work back to a business use case |

## What I already know

I am comfortable with SQL, Redshift views, Power BI modelling, reporting logic, reconciliations and checking results against business expectations. I also have experience with AWS Glue and Python in my current work.

## What I still need to prove to myself

- Whether the model grain is clear enough before I build on it
- How to organise dbt models so they remain understandable
- How to test failures without hiding them in the final output
- How to make reruns safe
- Which parts should be handled in SQL and which belong in Python
- How much orchestration is useful for a project of this size

## Future mapping, not current implementation

| Local version | Possible production equivalent |
|---|---|
| Local files | S3 landing area |
| Python or Spark load | Glue job |
| Local analytical database | Redshift |
| Local scheduled run | Airflow or another scheduler |
| Local tests | CI checks before a merge |

This mapping is an investigation list. It is not evidence that this repository is running on AWS.
