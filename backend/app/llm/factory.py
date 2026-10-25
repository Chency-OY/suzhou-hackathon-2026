from ..config import settings
from .mock import MockLLM
from .provider import LLMProvider


def get_provider() -> LLMProvider:
    if settings.llm_provider == "mock":
        return MockLLM()
    if settings.llm_provider == "openai_compat":
        from .openai_compat import OpenAICompatProvider
        return OpenAICompatProvider()
    raise ValueError(f"未知的 LLM_PROVIDER: {settings.llm_provider}")
