# Day 1 — setting the project up

**Date:** 14 August 2026

## Why I am doing this

I want to move towards analytics engineering without throwing away the experience I already have in reporting, SQL, Power BI, Redshift, Glue/Python, regulatory work and reconciliations.

A lot of my current work is production work, but I cannot put the underlying company data on GitHub. This repository gives me somewhere to practise the engineering parts openly using data that I generate myself.

## What I decided today

I am starting locally instead of connecting to AWS. That keeps the project free and means I can focus on the design before worrying about infrastructure.

I have started with a small Python package, a test, a rough architecture and an initial data contract. I have not generated any useful data yet.

## What I am deliberately not claiming

This will not prove that I have operated every tool in production. For example, a documented Glue or Airflow pattern is not the same as owning a live platform. My actual work experience will provide the production evidence; this repository is mainly for showing how I learn, structure and validate the work.

## Things I need to work out

- What the synthetic business rules should be
- How to keep the entity grain clear
- How to introduce realistic bad data
- Where SQL is the better choice than Python
- How to make the final outputs reconcile back to the inputs

## Next session

Generate the first synthetic customers, loans, subscriptions and payments with a fixed seed. Before adding more tables, check whether the keys and relationships make sense.
