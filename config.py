"""GEO 可见度诊断师 — 配置管理

使用 pydantic-settings 从 .env 文件加载配置，支持环境变量覆盖。
同时调用 python-dotenv 的 load_dotenv，确保 os.environ 也能获取 .env 中的变量，
供 stages/ 中直接读取环境变量的代码使用。
"""

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 加载 .env 到 os.environ，使 os.environ.get(...) 也能读取 .env 中的值
# override=True 保证 .env 文件优先于系统环境变量（避免系统残留旧 key 干扰）
load_dotenv(dotenv_path=".env", encoding="utf-8", override=True)


class Settings(BaseSettings):
    """GEO 可见度诊断师全局配置。

    配置优先级：环境变量 > .env 文件 > 默认值
    """

    # ── API Key 与 URL ──
    kimi_api_key: str = ""
    kimi_api_url: str = "https://api.moonshot.cn/v1/chat/completions"

    doubao_api_key: str = ""
    doubao_api_url: str = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

    openai_api_key: str = ""
    openai_api_url: str = "https://api.openai.com/v1/chat/completions"

    perplexity_api_key: str = ""
    perplexity_api_url: str = "https://api.perplexity.ai/chat/completions"

    serpapi_key: str = ""
    bing_search_key: str = ""

    # ── 运行参数 ──
    default_platform: str = "doubao"
    max_concurrent_searches: int = 3
    request_timeout: int = 30

    # ── 调试参数 ──
    debug: bool = False
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # 忽略未定义的环境变量，避免报错


# 全局单例
settings = Settings()
