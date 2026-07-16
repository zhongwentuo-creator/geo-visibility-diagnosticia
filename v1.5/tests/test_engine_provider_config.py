from __future__ import annotations

import importlib
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def test_stage1_uses_kimi_when_only_kimi_key_is_configured(monkeypatch):
    monkeypatch.setenv("KIMI_API_KEY", "test-kimi-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.setenv("KIMI_API_URL", "https://api.moonshot.cn/v1")
    monkeypatch.delenv("KIMI_MODEL", raising=False)

    from stages import s1_user_profile

    stage1 = importlib.reload(s1_user_profile)

    assert stage1.LLM_API_KEY == "test-kimi-key"
    assert stage1.LLM_API_URL == "https://api.moonshot.cn/v1/chat/completions"
    assert stage1.LLM_MODEL == "moonshot-v1-8k"


def test_api_client_routes_kimi_key_to_moonshot(monkeypatch):
    monkeypatch.setenv("KIMI_API_KEY", "test-kimi-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("KIMI_API_URL", raising=False)

    from utils import api_client

    assert api_client._get_openai_key() == "test-kimi-key"
    assert api_client._get_openai_url() == "https://api.moonshot.cn/v1"
    assert (
        api_client._resolve_model("gpt-4o", api_client._get_openai_url())
        == "moonshot-v1-8k"
    )
