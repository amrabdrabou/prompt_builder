---
description: Create a new Alembic database migration for a schema change in backend/models.py
---

# Add Database Migration

Follow these steps to create a new Alembic migration:

1. Read `backend/models.py` to understand the current schema.
2. Apply the requested model change to `backend/models.py`.
3. Generate the migration:
   ```bash
   cd backend && alembic revision --autogenerate -m "<short description>"
   ```
4. Read the generated file in `backend/migrations/versions/` and verify:
   - The `upgrade()` function correctly reflects the intended change
   - The `downgrade()` function correctly reverses it
   - No unexpected tables or columns appear in the diff
5. If the migration looks correct, apply it:
   ```bash
   cd backend && alembic upgrade head
   ```
6. Report the migration filename and a summary of what changed.

**Conventions:**
- Migration message should be snake_case and describe the change (e.g. `add_title_to_conversations`)
- Never edit existing migration files — always create a new one
- If the DB is running in Docker, run alembic inside the container or against the exposed port
