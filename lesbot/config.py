import tomllib
from os import PathLike

from pydantic import BaseModel, PositiveInt


class AttachmentConfig(BaseModel):
    mime_type_detect_buffer_size: PositiveInt
    mime_type_blacklist: list[str]


class ReactionRoleConfig(BaseModel):
    permitted_role_ids: list[int]


class BotConfig(BaseModel):
    attachments: AttachmentConfig
    reaction_roles: ReactionRoleConfig


def read_from(path: str | bytes | PathLike):
    with open(path, mode="rb") as f:
        return BotConfig(**tomllib.load(f))
