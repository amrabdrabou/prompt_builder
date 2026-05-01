---
description: Test the /chat endpoint with a sample message and inspect the response
---

# Test Chat Endpoint

Run a quick end-to-end test of the `/chat` endpoint:

**Start a new conversation:**
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_message": "I need a prompt for a customer support chatbot"}' | python3 -m json.tool
```

**Continue an existing conversation (replace `<id>` with the conversation_id from above):**
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_message": "It should handle billing and refunds", "conversation_id": "<id>"}' | python3 -m json.tool
```

**Health check:**
```bash
curl -s http://localhost:8000/ | python3 -m json.tool
```

After running, inspect the response and report:
- Whether `action` is `ask_question` or `final_prompt`
- Whether the `message`/`prompt` content is appropriate
- Any errors or unexpected fields in the response

If the server is not running, start it first:
```bash
cd backend && uvicorn main:app --reload
```
