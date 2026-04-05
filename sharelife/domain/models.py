"""Core domain models for template manifests."""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class TemplateManifest(BaseModel):
    template_id: str
    version: str
    title_i18n: dict[str, str]
    astrbot_version: str | None = None
    summary_i18n: dict[str, str] = Field(default_factory=dict)
    prompt_template: str = ""
    risk_level: str = "low"
    review_labels: list[str] = Field(default_factory=list)
    warning_flags: list[str] = Field(default_factory=list)
    scan_summary: dict[str, Any] = Field(default_factory=dict)
    category: str = ""
    tags: list[str] = Field(default_factory=list)
    maintainer: str = ""
    source_channel: str = ""

    @field_validator("title_i18n")
    @classmethod
    def ensure_required_locales(cls, value: dict[str, str]) -> dict[str, str]:
        required = {"zh-CN", "en-US"}
        if not required.issubset(value.keys()):
            raise ValueError("title_i18n must contain zh-CN and en-US")
        return value
