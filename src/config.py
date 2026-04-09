import os
from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    ph_token: str = Field(alias="PH_TOKEN")
    lark_app_id: str = Field(alias="LARK_APP_ID")
    lark_app_secret: str = Field(alias="LARK_APP_SECRET")
    lark_chat_id: str = Field(alias="LARK_CHAT_ID")
    lark_base_app_token: str = Field(alias="LARK_BASE_APP_TOKEN")
    lark_base_table_id: str = Field(alias="LARK_BASE_TABLE_ID")
    summary_api_key: str = Field(alias="SUMMARY_API_KEY")
    summary_base_url: str = Field(default="https://api.siliconflow.cn/v1", alias="SUMMARY_BASE_URL")
    summary_model: str = Field(default="deepseek-ai/DeepSeek-V3", alias="SUMMARY_MODEL")
    summary_fallback_models: list[str] = Field(default_factory=list, alias="SUMMARY_FALLBACK_MODELS")

    def __init__(self, **kwargs):
        raw_fallback = os.environ.get("SUMMARY_FALLBACK_MODELS", "")
        if not kwargs.get("summary_fallback_models"):
            if raw_fallback.strip():
                kwargs["summary_fallback_models"] = [
                    m.strip() for m in raw_fallback.split(",") if m.strip()
                ]
            else:
                kwargs["summary_fallback_models"] = []
            # Prevent BaseSettings from re-reading the raw env var and doing json.loads on it.
            os.environ.pop("SUMMARY_FALLBACK_MODELS", None)
        super().__init__(**kwargs)
