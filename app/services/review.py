from __future__ import annotations

import re

from app.core.config import Settings
from app.schemas.review import (
    KnowledgeBaseState,
    ReviewFileRequest,
    ReviewGitHubPRRequest,
    ReviewPRRequest,
    ReviewResponse,
    SetupResponse,
    StandardRecord,
    StandardsResponse,
    WeeklyDigestResponse,
)
from app.services.notion import NotionService
from app.services.reviewer import HFReviewEngine
from app.services.state import StateStore


class SetupRequiredError(RuntimeError):
    pass


MAX_GITHUB_PR_FILES = 20
MAX_GITHUB_DIFF_CHARS = 120_000
GITHUB_PR_URL_RE = re.compile(r"^https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)/?$")


def parse_github_pr_url(pr_url: str) -> tuple[str, str, int]:
    match = GITHUB_PR_URL_RE.match(pr_url.strip())
    if not match:
        raise ValueError("Invalid GitHub PR URL. Expected: https://github.com/owner/repo/pull/123")
    owner, repo, pull_number = match.group(1), match.group(2), int(match.group(3))
    return owner, repo, pull_number


class ReviewService:
    def __init__(
        self,
        *,
        reviewer: HFReviewEngine,
        notion_service: NotionService,
        state_store: StateStore,
        notion_parent_page_id: str,
        settings: Settings | None = None,
    ) -> None:
        self.reviewer = reviewer
        self.notion_service = notion_service
        self.state_store = state_store
        self.notion_parent_page_id = notion_parent_page_id
        self.settings = settings

    async def close(self) -> None:
        await self.notion_service.close()

    async def setup(self, force: bool = False) -> SetupResponse:
        self._require_notion_config()
        existing_state = self.state_store.load()
        if existing_state is not None and not force:
            return SetupResponse(
                **existing_state.model_dump(),
                logs=["Using existing cached Notion knowledge base. Pass force=true to rebuild it."],
            )

        state, logs = await self.notion_service.setup_workspace(self.notion_parent_page_id)
        self.state_store.save(state)
        return SetupResponse(**state.model_dump(), logs=logs)

    async def review_pr(self, request: ReviewPRRequest) -> ReviewResponse:
        state = self._require_state()
        analysis = await self.reviewer.review_diff(
            diff=request.diff,
            pr_title=request.pr_title,
            repo=request.repo,
        )
        notion_result = await self.notion_service.persist_review(
            analysis=analysis,
            pr_title=request.pr_title,
            repo=request.repo,
            state=state,
        )
        return ReviewResponse(
            issues=analysis.issues,
            notion_url=notion_result.notion_url,
            standards_updated=notion_result.standards_updated,
            logs=[f"AI found {len(analysis.issues)} issues.", *notion_result.activity],
        )

    async def review_file(self, request: ReviewFileRequest) -> ReviewResponse:
        state = self._require_state()
        analysis = await self.reviewer.review_file(
            filename=request.filename,
            content=request.content,
            pr_title=request.pr_title,
            repo=request.repo,
        )
        notion_result = await self.notion_service.persist_review(
            analysis=analysis,
            pr_title=request.pr_title,
            repo=request.repo,
            state=state,
        )
        return ReviewResponse(
            issues=analysis.issues,
            notion_url=notion_result.notion_url,
            standards_updated=notion_result.standards_updated,
            logs=[f"AI found {len(analysis.issues)} issues.", *notion_result.activity],
        )

    async def review_github_pr(self, request: ReviewGitHubPRRequest) -> ReviewResponse:
        """Fetch PR diff via GitHub MCP, then review and persist to Notion."""
        if self.settings is None or not self.settings.github_token:
            raise RuntimeError("GITHUB_TOKEN not configured. Set it in .env to use GitHub MCP.")
        state = self._require_state()
        owner, repo, pull_number = parse_github_pr_url(request.pr_url)

        from app.services.mcp_client import github_session, mcp_call

        # Fetch PR info and files via GitHub MCP
        async with github_session(self.settings) as gh:
            pr_info = await mcp_call(gh, "get_pull_request", {
                "owner": owner, "repo": repo, "pull_number": pull_number,
            })
            pr_files = await mcp_call(gh, "get_pull_request_files", {
                "owner": owner, "repo": repo, "pull_number": pull_number,
            })

        pr_title = pr_info.get("title", f"PR #{pull_number}")
        repo_full = f"{owner}/{repo}"

        # Build a combined diff from file patches
        diff_parts = []
        file_items = pr_files if isinstance(pr_files, list) else pr_files.get("files", pr_files.get("results", []))
        for f in file_items[:MAX_GITHUB_PR_FILES]:
            patch = f.get("patch", "")
            if patch:
                diff_parts.append(f"--- a/{f.get('filename', '?')}\n+++ b/{f.get('filename', '?')}\n{patch}")
        combined_diff = "\n".join(diff_parts) if diff_parts else "No diff available."
        if len(combined_diff) > MAX_GITHUB_DIFF_CHARS:
            combined_diff = combined_diff[:MAX_GITHUB_DIFF_CHARS] + "\n... [Diff truncated]"

        # Review with HF
        analysis = await self.reviewer.review_diff(
            diff=combined_diff, pr_title=pr_title, repo=repo_full,
        )

        # Persist to Notion
        notion_result = await self.notion_service.persist_review(
            analysis=analysis, pr_title=pr_title, repo=repo_full, state=state,
        )

        return ReviewResponse(
            issues=analysis.issues,
            notion_url=notion_result.notion_url,
            standards_updated=notion_result.standards_updated,
            logs=[
                f"Fetched PR #{pull_number} from {repo_full} via GitHub MCP.",
                f"PR: {pr_title} ({len(diff_parts)} files changed).",
                f"AI found {len(analysis.issues)} issues.",
                *notion_result.activity,
            ],
        )

    async def get_standards(self) -> StandardsResponse:
        state = self._require_state()
        rules, logs = await self.notion_service.fetch_standards(state)
        return StandardsResponse(rules=rules, logs=logs)

    async def weekly_digest(self) -> WeeklyDigestResponse:
        state = self._require_state()
        digest = await self.notion_service.create_weekly_digest(state)
        return WeeklyDigestResponse(
            report_title=digest.report_title,
            notion_url=digest.notion_url,
            summary=digest.summary,
            logs=digest.activity,
        )

    def _require_state(self) -> KnowledgeBaseState:
        state = self.state_store.load()
        if state is None:
            raise SetupRequiredError("Run POST /api/setup before using review or digest endpoints.")
        return state

    def _require_notion_config(self) -> None:
        if self.settings is not None:
            if not self.settings.notion_token:
                raise RuntimeError("NOTION_TOKEN not configured. Set it in .env before running setup.")
            if not self.settings.notion_parent_page_id:
                raise RuntimeError("NOTION_PARENT_PAGE_ID not configured. Set it in .env before running setup.")
        elif not self.notion_parent_page_id:
            raise RuntimeError("NOTION_PARENT_PAGE_ID not configured. Set it in .env before running setup.")
