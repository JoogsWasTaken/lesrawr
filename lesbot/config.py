import tomllib
from os import PathLike

from pydantic import BaseModel, PositiveInt


class AttachmentConfig(BaseModel):
    mime_type_detect_buffer_size: PositiveInt
    mime_type_blacklist: list[str]


class BotConfig(BaseModel):
    attachments: AttachmentConfig


def read_from(path: str | bytes | PathLike):
    with open(path, mode="rb") as f:
        return BotConfig(**tomllib.load(f))
