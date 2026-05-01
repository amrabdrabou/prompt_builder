---
description: Review and improve the agent's system prompt in backend/prompts.py for clarity, consistency, and effectiveness
---

# Review System Prompt

Read `backend/prompts.py` and `backend/agent.py` in full, then analyze the system prompt critically.

Evaluate:
1. **Ambiguity** — instructions the LLM might misinterpret or apply inconsistently
2. **Redundancy** — repeated rules that add noise without adding clarity
3. **Missing constraints** — edge cases not covered (e.g. user sends gibberish, user asks agent to do the task instead of building a prompt)
4. **JSON contract alignment** — does the prompt accurately describe the JSON schema enforced in `agent.py`?
5. **Question strategy** — does the prompt guide the agent to ask the right number of questions before finalizing?
6. **Tone and conciseness** — is the prompt longer than it needs to be?

For each issue found: quote the problematic text, explain the problem, and propose a specific rewrite.
At the end, provide the full improved prompt ready to drop into `prompts.py`.
