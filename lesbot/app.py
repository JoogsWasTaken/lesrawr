import inspect
import logging
import os
import sys
from pathlib import Path

import discord
import magic
import requests
from discord.ext import commands
from dotenv import load_dotenv
from loguru import logger
from pydantic import ValidationError
from tinydb import TinyDB, Query

import lesbot.config
from lesbot.config import BotConfig


# set all standard logging to go through loguru instead, see:
# https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

# start fresh
logger.remove()
# add info level logs to stderr and debug level logs to log directory
logger.add(
    sys.stderr,
    colorize=True,
    format="<green>{time}</green> | {name} | <level>{level}</level> | <level>{message}</level>",
    level="INFO",
)
logger.add(
    Path(__file__).parent / ".." / "logs" / "lesrawr_{time}.log",
    rotation="1 day",
    retention="5 days",
    compression="tar.gz",
    level="DEBUG",
)

activity = discord.Activity(
    type=discord.ActivityType.watching, name="🦁 Ich fresse deine Anhänge"
)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

config: BotConfig
client = commands.Bot(command_prefix="!", intents=intents, activity=activity)


@client.event
async def on_ready():
    logger.info("Logged in as {}", client.user)


def obtain_mime_type_from_attachment(attachment: discord.Attachment):
    # "impersonating" the http client from discord.py. this is basically how any
    # http request is performed in the library. the header fields are taken from
    # the request() function in the discord.http.HTTPClient class. the reason we're
    # doing it manually is that discord.py doesn't allow for an arbitrary amount
    # of bytes to be read from an attachment. magic-python only requires 2048 bytes
    # for accurate results. so we're manually requesting the attachment's content
    # and only extracting as many bytes as we need from it to save bandwidth, disk
    # space and processing time. is this overengineering? yes!
    with requests.get(
        attachment.url,
        headers={
            "User-Agent": client.http.user_agent,
            "Authorization": f"Bot {client.http.token}",
        },
        stream=True,
    ) as r:
        content_iter = r.iter_content(
            chunk_size=config.attachments.mime_type_detect_buffer_size
        )
        # single call to next() exhausts the iterator. then we can close the request.
        attachment_content = next(content_iter)

    return magic.from_buffer(attachment_content, mime=True)


# TinyDB for saving the reactionroles
db = TinyDB("database.json")
User = Query()
required_role_id = 1241433186710585496


@client.command()
async def remove_reaction_role(ctx, message_ID, Emoji):
    # check if user is authorized
    if not any(role.id == required_role_id for role in ctx.author.roles):
        await ctx.send("Du hast keine rechte hierfür!")
        return

    # checks, if the message id is in the database
    data = db.get(User.message_ID == str(message_ID))
    if data is None:
        await ctx.send(
            f"Keine Reaction-Rolle gefunden für die Nachricht mit der ID {message_ID}."
        )
        return

    # Searching the roles in the message for the role with the specified emoji
    for role_entry in data["roles"]:
        if role_entry["Emoji"] == Emoji:
            # remove role from the database
            data["roles"].remove(role_entry)
            db.update({"roles": data["roles"]}, User.message_ID == str(message_ID))

            # remove reaction
            message = await ctx.fetch_message(message_ID)
            await message.remove_reaction(Emoji, client.user)

            await ctx.send(
                f"Reaction-Rolle mit dem Emoji {Emoji} wurde aus der Nachricht mit der ID {message_ID} entfernt."
            )
            return

    # If emoji wasn't found
    await ctx.send(
        f"Keine Reaction-Rolle gefunden für das Emoji {Emoji} in der Nachricht mit der ID {message_ID}."
    )


# add reactionroles
@client.command()
async def add_reaction_role(ctx, Rolle, message_ID, Emoji):
    # check if user is authorized
    if not any(role.id == required_role_id for role in ctx.author.roles):
        await ctx.send("Du hast keine rechte hierfür!")
        return

    role = discord.utils.get(ctx.guild.roles, name=Rolle)
    if role is None:
        await ctx.send(f"Rolle {Rolle} nicht gefunden")
        return
    role_ID = role.id

    db.upsert(
        {
            "message_ID": str(message_ID),
            "roles": [{"role_ID": role_ID, "Emoji": Emoji}],
        },
        User.message_ID == str(message_ID),
    )

    message = await ctx.fetch_message(message_ID)
    await message.add_reaction(Emoji)
    await ctx.send(
        f"Die Rolle {Rolle} wurde dem Emoji {Emoji} hinzugefügt unter der Message ID {message_ID}"
    )


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Du hast ein Argument vergessen hinzuzufügen!")


# giving roles
@client.event
async def on_raw_reaction_add(payload):
    if payload.guild_id is None:
        return

    guild = client.get_guild(payload.guild_id)
    if guild is None:
        return

    # getting message id from database
    data = db.get(User.message_ID == str(payload.message_id))
    if data is None:
        return

    for role_entry in data["roles"]:
        if role_entry["Emoji"] == str(payload.emoji):
            role = guild.get_role(role_entry["role_ID"])
            if role is None:
                continue

            member = guild.get_member(payload.user_id)
            if member is None:
                continue

            # error handling
            try:
                await member.add_roles(role)
            except discord.errors.Forbidden:
                logger.opt(exception=True).error(
                    f"Fehlende Berechtigungen, um die Rolle {role.name} zuzuweisen."
                )
                return


# removes roles
@client.event
async def on_raw_reaction_remove(payload):
    if payload.guild_id is None:
        return

    guild = client.get_guild(payload.guild_id)
    if guild is None:
        return

    # Get message id from database
    data = db.get(User.message_ID == str(payload.message_id))
    if data is None:
        return

    for role_entry in data["roles"]:
        if role_entry["Emoji"] == str(payload.emoji):
            role = guild.get_role(role_entry["role_ID"])
            if role is None:
                continue

            member = guild.get_member(payload.user_id)
            if member is None:
                continue

            # Error Handling
            try:
                await member.remove_roles(role)
            except discord.errors.Forbidden:
                logger.opt(exception=True).error(
                    f"Fehlende Berechtigungen, um die Rolle {role.name} zu entfernen."
                )
                return


@client.listen()
async def on_message(message: discord.Message):
    # ignore messages from bot
    if message.author == client.user:
        return

    # ignore messages that were not sent in a guild
    if message.guild is None:
        return

    # ignore messages from bots
    if message.author.bot:
        return

    # ignore messages without attachments
    if len(message.attachments) == 0:
        return

    # start processing attachments
    for attachment in message.attachments:
        attachment_mime = obtain_mime_type_from_attachment(attachment)
        logger.debug(
            "Attachment {} of message {} by {} has MIME type {}",
            attachment.filename,
            message.id,
            message.author.name,
            attachment_mime,
        )

        if attachment_mime not in config.attachments.mime_type_blacklist:
            continue

        logger.info("Found blacklisted attachment in message {}, deleting", message.id)

        await message.delete()
        await message.author.send(
            f"Hey! Deine Nachricht in {message.channel.jump_url} wurde gelöscht weil sie einen Anhang enthielt, "
            f"der auf dem Server nicht gestattet ist. Bitte lade den Anhang in die "
            f"[Leipzig eSports Cloud](https://cloud.leipzigesports.de/) hoch und verlinke ihn im Chat."
        )

        # don't need to go over any extra attachments
        break
    await client.process_commands(message)


def run():
    global config

    try:
        config = lesbot.config.read_from(
            Path(__file__).parent / ".." / "config" / "app.toml"
        )
    except ValidationError:
        logger.opt(exception=True).error("Failed to validate config file")
        exit(1)

    load_dotenv()
    token = os.environ.get("DISCORD_BOT_TOKEN", None)

    if token is None:
        logger.error(
            "Bot token not set, use `{}` environment variable", "DISCORD_BOT_TOKEN"
        )
        exit(2)

    client.run(token, log_handler=None)


if __name__ == "__main__":
    run()
