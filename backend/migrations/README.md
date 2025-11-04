# Database Migrations

This directory contains Alembic database migration scripts.

## Initialize Alembic

```bash
alembic init migrations
```

## Create New Migration

```bash
alembic revision --autogenerate -m "description"
```

## Run Migrations

```bash
alembic upgrade head
```

## Rollback Migration

```bash
alembic downgrade -1
```
