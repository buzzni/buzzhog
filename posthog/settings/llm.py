import os

# Provider credentials for the LLM features. A feature whose key is empty reports itself unavailable.
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL: str | None = os.getenv("OPENAI_BASE_URL") or None
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
REPLAY_VISION_GEMINI_API_KEY: str = os.getenv("REPLAY_VISION_GEMINI_API_KEY", "")
INKEEP_API_KEY: str = os.getenv("INKEEP_API_KEY", "")

LLM_GATEWAY_URL: str = os.getenv("LLM_GATEWAY_URL", "")
LLM_GATEWAY_API_KEY: str = os.getenv("LLM_GATEWAY_API_KEY", "")
