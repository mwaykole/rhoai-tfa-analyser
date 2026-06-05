"""Configuration management using Pydantic Settings."""

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ReportPortalConfig(BaseSettings):
    """ReportPortal connection configuration."""

    url: str = Field(..., description="ReportPortal server URL")
    token: str | None = Field(default=None, description="ReportPortal API token")
    username: str | None = Field(default=None, description="ReportPortal username")
    password: str | None = Field(default=None, description="ReportPortal password")
    project: str = Field(..., description="ReportPortal project name")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")

    @field_validator("url")
    @classmethod
    def strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Log level"
    )
    format: Literal["json", "console"] = Field(
        default="json", description="Log format"
    )


class RetrySettings(BaseSettings):
    """Retry behavior configuration."""

    max_attempts: int = Field(default=3, ge=1, le=10, description="Max retry attempts")
    base_delay: float = Field(default=1.0, ge=0.1, description="Base delay in seconds")
    max_delay: float = Field(default=30.0, ge=1.0, description="Max delay in seconds")
    exponential_base: float = Field(default=2.0, ge=1.1, description="Backoff base")


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_prefix="",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    reportportal: ReportPortalConfig
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    retry: RetrySettings = Field(default_factory=RetrySettings)

    rp_url: str | None = Field(default=None, alias="RP_URL")
    rp_token: str | None = Field(default=None, alias="RP_TOKEN")
    rp_username: str | None = Field(default=None, alias="RP_USERNAME")
    rp_password: str | None = Field(default=None, alias="RP_PASSWORD")
    rp_project: str | None = Field(default=None, alias="RP_PROJECT")

    def get_rp_url(self) -> str:
        url = self.rp_url or self.reportportal.url
        if not url or url.startswith("${"):
            raise ValueError("RP_URL environment variable is required")
        return url

    def get_rp_token(self) -> str | None:
        token = self.rp_token or self.reportportal.token
        if token and token.startswith("${"):
            return None
        return token or None

    def get_rp_username(self) -> str | None:
        username = self.rp_username or self.reportportal.username
        if username and username.startswith("${"):
            return None
        return username or None

    def get_rp_password(self) -> str | None:
        password = self.rp_password or self.reportportal.password
        if password and password.startswith("${"):
            return None
        return password or None

    def get_rp_project(self) -> str:
        project = self.rp_project or self.reportportal.project
        if not project or project.startswith("${"):
            raise ValueError("RP_PROJECT environment variable is required")
        return project

    def get_rp_auth(self) -> tuple[str | None, str | None, str | None]:
        """Get ReportPortal authentication credentials.

        Returns:
            Tuple of (token, username, password)
        """
        return (self.get_rp_token(), self.get_rp_username(), self.get_rp_password())


def load_yaml_config(config_path: Path) -> dict:
    """Load configuration from YAML file with environment variable substitution."""
    if not config_path.exists():
        return {}

    with open(config_path) as f:
        content = f.read()

    def replace_env_var(match: re.Match) -> str:
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))

    content = re.sub(r"\$\{(\w+)\}", replace_env_var, content)
    return yaml.safe_load(content) or {}


def create_settings(config_path: Path | None = None) -> Settings:
    """Create settings from config file and environment variables."""
    from dotenv import load_dotenv

    load_dotenv(override=True)

    config_data: dict = {}

    if config_path and config_path.exists():
        config_data = load_yaml_config(config_path)
    else:
        default_path = Path("config.yaml")
        if default_path.exists():
            config_data = load_yaml_config(default_path)

    rp_defaults = {
        "url": os.environ.get("RP_URL", ""),
        "token": os.environ.get("RP_TOKEN", ""),
        "username": os.environ.get("RP_USERNAME", ""),
        "password": os.environ.get("RP_PASSWORD", ""),
        "project": os.environ.get("RP_PROJECT", ""),
    }
    if "reportportal" in config_data:
        for key, val in rp_defaults.items():
            if val and key not in config_data["reportportal"]:
                config_data["reportportal"][key] = val
    else:
        config_data["reportportal"] = rp_defaults

    return Settings(**config_data)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return create_settings()
