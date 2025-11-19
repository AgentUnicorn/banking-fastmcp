import os
from typing import List, Literal

from dotenv import load_dotenv

load_dotenv()


class Settings:
    BASE_URL: str = os.environ.get("RS_BASE_URL", "http://localhost:8005")
    HOST: str = os.environ.get("RS_HOST", "localhost")
    PORT: int = int(os.environ.get("RS_PORT", "8005"))
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "banking.db")
    MCP_PATH: str = os.environ.get("MCP_PATH", "/mcp")
    ENVIRONMENT: Literal["develop", "production"] = os.environ.get(
        "ENVIRONMENT", "develop"
    )
    AUTHENTICATE_PROVIDER: Literal["jwt", "scalekit"] = "jwt"

    RESOURCE: str = f"{BASE_URL}{MCP_PATH}"

    # ScaleKit Configuration
    SCALEKIT_ENVIRONMENT_URL: str = os.environ.get("SCALEKIT_ENVIRONMENT_URL", "")
    SCALEKIT_CLIENT_ID: str = os.environ.get("SCALEKIT_CLIENT_ID", "")
    SCALEKIT_CLIENT_SECRET: str = os.environ.get("SCALEKIT_CLIENT_SECRET", "")
    SCALEKIT_RESOURCE_METADATA_URL: str = os.environ.get(
        "SCALEKIT_RESOURCE_METADATA_URL", ""
    )
    SCALEKIT_AUDIENCE_NAME: str = os.environ.get("SCALEKIT_AUDIENCE_NAME", "")
    METADATA_JSON_RESPONSE: str = os.environ.get("METADATA_JSON_RESPONSE", "")


settings = Settings()
