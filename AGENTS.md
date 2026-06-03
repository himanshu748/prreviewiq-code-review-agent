# PRReviewIQ Agent Notes

## Project Shape
- FastAPI dashboard and CLI for reviewing diffs/files and persisting insights into a Notion knowledge base.
- `app/services/review.py` orchestrates review, GitHub PR fetching, state checks, and Notion persistence.
- `app/services/mcp_client.py` owns MCP/Notion integration helpers; keep external MCP dependencies lazy enough for tests and health routes.
- Local runtime state lives under `.prreviewiq/` and must not be committed.

## Common Commands
- Tests: `python -m pytest`
- Syntax check: `python -m compileall app tests review.py`
- Dev server: `uvicorn app.main:app --reload`
- CLI: `python review.py --repo /path/to/repo`

## Conventions
- Do not commit Notion state, tokens, page IDs, `.env`, caches, or generated outputs.
- Keep setup/review endpoints explicit about missing `HF_API_KEY`, `NOTION_TOKEN`, `NOTION_PARENT_PAGE_ID`, or `GITHUB_TOKEN`.
- Bound raw diff/file inputs before sending them to Hugging Face or Notion.
- Keep direct Notion REST fallback documented as a fallback; primary product copy should still describe the MCP path.
