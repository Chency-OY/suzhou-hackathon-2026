import sys

sys.path.insert(0, "backend")
from pydantic import BaseModel  # noqa: E402

from app.llm import get_provider, get_tracker, load_prompt, structured_call  # noqa: E402


class Echo(BaseModel):
    echo: str


def main() -> int:
    provider = get_provider()
    if provider.name == "mock":
        print("当前 LLM_PROVIDER=mock，未做真实调用。请在 .env 配置 openai_compat 后再运行。")
        return 0
    prompt = load_prompt("_example")
    out, degraded = structured_call(
        provider, prompt_name="smoke", system="你是严格只输出 JSON 的助手。",
        messages=[{"role": "user", "content": prompt.render(text="你好")}],
        model_cls=Echo, fallback=Echo(echo=""), max_retries=1, temperature=0.2)
    print("provider:", provider.name, "| degraded:", degraded, "| echo:", out.echo)
    print("usage:", get_tracker().summary())
    return 0 if (not degraded and out.echo) else 1


if __name__ == "__main__":
    sys.exit(main())
