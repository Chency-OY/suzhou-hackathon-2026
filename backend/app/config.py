from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "mock"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_json_mode: bool = True
    llm_timeout_s: float = 90.0
    daily_token_cap: int = 0
    usage_dir: str = "data/usage"
    db_url: str = "sqlite:///./data/app.db"
    prompts_dir: str = "prompts"
    embed_provider: str = "hash"      # hash | openai_compat
    embed_base_url: str = ""
    embed_api_key: str = ""
    embed_model: str = ""
    vector_store: str = "chroma"      # chroma | simple
    chroma_dir: str = "data/chroma"


settings = Settings()
