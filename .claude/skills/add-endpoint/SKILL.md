---
description: Add a new FastAPI endpoint to backend/main.py following project conventions
---

# Add Endpoint

Read `backend/main.py`, `backend/schemas.py`, `backend/memory.py`, and `backend/models.py` before writing anything.

Follow these conventions from the existing codebase:

**Structure:**
- Define request/response Pydantic models in `schemas.py` first
- Add DB helper functions to `memory.py` if new queries are needed
- Add the route to `main.py` using `async def` with `db: AsyncSession = Depends(get_db)`

**Error handling pattern (match existing endpoints):**
```python
try:
    # business logic
except HTTPException:
    raise
except Exception as error:
    logger.exception("...")
    raise HTTPException(status_code=500, detail="...") from error
```

**Response models:**
- Always set `response_model=` on the route decorator
- Use a discriminated union via `AgentResponse = Union[...]` if the route can return multiple shapes

After implementing, describe what was added and how to call the new endpoint with a curl example.
