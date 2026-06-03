# PRReviewIQ

PRReviewIQ is a local FastAPI app plus Python CLI that reviews pull request diffs with HuggingFace and logs every review insight into a Notion knowledge base through Notion MCP.

## What it does

- `POST /api/setup` provisions the Notion workspace structure.
- `POST /api/review-pr` reviews a raw git diff and logs findings.
- `POST /api/review-file` reviews a single file for pre-commit style checks.
- `GET /api/standards` returns the living coding standards database as JSON.
- `POST /api/weekly-digest` creates a weekly quality report page in Notion.
- `python review.py --repo /path/to/repo` runs the CLI against a local git repo.

## Important Notion MCP note

This implementation uses the official `@notionhq/notion-mcp-server` package locally via `npx`, with `NOTION_TOKEN` passed to the MCP server, so all Notion writes still happen through MCP and never through direct REST calls from this app.

## Prerequisites

- Python 3.11+
- Node.js and `npx`
- A Notion integration token in `NOTION_TOKEN`
- A parent Notion page ID in `NOTION_PARENT_PAGE_ID`
- A HuggingFace API key in `HF_API_KEY`

## Run locally

```bash
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## CLI examples

```bash
python review.py --repo /path/to/repo
python review.py --file path/to/file.py --pr-title "Pre-commit review" --repo-name my-repo
```

## Verification

```bash
python -m pytest
python -m compileall app tests review.py
```

The app can serve health and static UI routes without tokens. Review/setup routes fail with explicit configuration errors until `HF_API_KEY`, `NOTION_TOKEN`, `NOTION_PARENT_PAGE_ID`, and optional `GITHUB_TOKEN` are configured. `/api/health` reports `notion_transport` so MCP stdio and REST fallback are not confused.

## Local state and secrets

- `.env` contains tokens and is ignored.
- `.prreviewiq/` contains local Notion workspace state created by setup and is ignored.
- Do not commit Notion page IDs, tokens, generated reports, or cache directories.

## Project layout

```text
app/
  api/
  core/
  schemas/
  services/
  static/
review.py
tests/
```
