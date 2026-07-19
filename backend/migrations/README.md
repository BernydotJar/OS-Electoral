# CampaignOS database migrations

Alembic owns the production schema. Run migrations only against an explicitly
selected database URL:

```bash
CAMPAIGNOS_DATABASE_URL='postgresql+psycopg://...' uv run alembic upgrade head
```

Migration files are reviewed source. Autogeneration is a starting point, never
an approval. Production migration requires backup, rehearsal, compatibility,
health, and rollback/forward-recovery evidence.
