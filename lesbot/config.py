import tomllib
from os import PathLike

from pydantic import BaseModel, PositiveInt, Field


class AttachmentConfig(BaseModel):
    mime_type_detect_buffer_size: PositiveInt
    mime_type_blacklist: list[str]


class GuildConfig(BaseModel):
    id: int
    permitted_role_ids: list[int]
    notification_channel_id: int


class BotConfig(BaseModel):
    attachments: AttachmentConfig
    guilds: list[GuildConfig] = Field(default_factory=list)


def read_from(path: str | bytes | PathLike):
    with open(path, mode="rb") as f:
        return BotConfig(**tomllib.load(f))
