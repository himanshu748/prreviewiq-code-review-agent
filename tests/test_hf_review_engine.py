import json

import pytest

from app.services.hf import HFError, HFService
from app.services.reviewer import (
    MAX_FILENAME_CHARS,
    MAX_REVIEW_TEXT_CHARS,
    MAX_TITLE_CHARS,
    HFReviewEngine,
)


class CapturingHF:
    def __init__(self) -> None:
        self.messages = []

    async def chat(self, *, system_prompt, messages, **kwargs) -> str:
        self.messages = messages
        return json.dumps(
            {
                "summary": "ok",
                "issues": [],
                "standards": [],
            }
        )


@pytest.mark.asyncio
async def test_review_diff_bounds_payload_before_hf_call():
    hf = CapturingHF()
    engine = HFReviewEngine(hf)

    await engine.review_diff(
        diff="D" * (MAX_REVIEW_TEXT_CHARS + 100),
        pr_title="T" * (MAX_TITLE_CHARS + 100),
        repo="demo/repo",
    )

    payload = json.loads(hf.messages[0]["content"])
    assert len(payload["diff"]) == MAX_REVIEW_TEXT_CHARS
    assert len(payload["pr_title"]) == MAX_TITLE_CHARS
    assert "D" * (MAX_REVIEW_TEXT_CHARS + 1) not in hf.messages[0]["content"]
    assert "T" * (MAX_TITLE_CHARS + 1) not in hf.messages[0]["content"]


@pytest.mark.asyncio
async def test_review_file_bounds_payload_before_hf_call():
    hf = CapturingHF()
    engine = HFReviewEngine(hf)

    await engine.review_file(
        filename="f" * (MAX_FILENAME_CHARS + 100),
        content="C" * (MAX_REVIEW_TEXT_CHARS + 100),
        pr_title="Demo",
        repo="demo/repo",
    )

    payload = json.loads(hf.messages[0]["content"])
    assert len(payload["filename"]) == MAX_FILENAME_CHARS
    assert len(payload["content"]) == MAX_REVIEW_TEXT_CHARS
    assert "f" * (MAX_FILENAME_CHARS + 1) not in hf.messages[0]["content"]
    assert "C" * (MAX_REVIEW_TEXT_CHARS + 1) not in hf.messages[0]["content"]


@pytest.mark.asyncio
async def test_hf_service_does_not_expose_raw_provider_exception():
    class BadClient:
        async def chat_completion(self, **kwargs):
            raise RuntimeError("provider leaked hf_secret_token")

    service = HFService(api_key="test-token", model="test-model")
    service._client = BadClient()

    with pytest.raises(HFError) as caught:
        await service.chat(system_prompt="review", messages=[])

    assert str(caught.value) == "HuggingFace request failed."
    assert "hf_secret_token" not in str(caught.value)
