import os
import re
from typing import Optional
from urllib.parse import urlparse

import aiohttp
import discord

PATCH_TITLE_RE = re.compile(r"League of Legends Patch\s+(\d+)\.(\d+)\s+Notes", re.IGNORECASE)
LOL_EN_PATH_RE = re.compile(
    r"^/(?:[a-z]{2}-[a-z]{2})?/??news/game-updates/(league-of-legends-patch-[\d-]+-notes)/?$",
    re.IGNORECASE,
)

TARGET_CHANNEL_IDS = {
    int(value.strip())
    for value in os.getenv("TARGET_CHANNEL_IDS", "").split(",")
    if value.strip().isdigit()
}

PATCHBOT_USER_IDS = {
    int(value.strip())
    for value in os.getenv("PATCHBOT_USER_IDS", "").split(",")
    if value.strip().isdigit()
}

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


async def resolve_redirect(url: str, timeout_seconds: float = 10.0) -> str:
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, allow_redirects=True) as response:
            return str(response.url)


def build_ja_url_from_url(url: str) -> Optional[str]:
    parsed = urlparse(url)
    if "leagueoflegends.com" not in parsed.netloc.lower():
        return None

    match = LOL_EN_PATH_RE.match(parsed.path)
    if not match:
        return None

    slug = match.group(1).lower()
    return f"https://www.leagueoflegends.com/ja-jp/news/game-updates/{slug}/"


def build_ja_url_from_patch_title(text: str) -> Optional[str]:
    match = PATCH_TITLE_RE.search(text)
    if not match:
        return None

    major, minor = match.groups()
    slug = f"league-of-legends-patch-{major}-{minor}-notes"
    return f"https://www.leagueoflegends.com/ja-jp/news/game-updates/{slug}/"


async def find_ja_patch_url(message: discord.Message) -> Optional[str]:
    candidate_urls = re.findall(r"https?://\S+", message.content)

    # Embed URL も対象にする
    for embed in message.embeds:
        if embed.url:
            candidate_urls.append(embed.url)
        if embed.title:
            built = build_ja_url_from_patch_title(embed.title)
            if built:
                return built

    # メッセージ本文のタイトル文字列からも判定
    built = build_ja_url_from_patch_title(message.content)
    if built:
        return built

    for raw_url in candidate_urls:
        cleaned = raw_url.rstrip(">).,\"")
        direct = build_ja_url_from_url(cleaned)
        if direct:
            return direct

        try:
            resolved = await resolve_redirect(cleaned)
        except Exception:
            continue

        converted = build_ja_url_from_url(resolved)
        if converted:
            return converted

    return None


def is_patchbot_message(message: discord.Message) -> bool:
    if not message.author.bot:
        return False

    if PATCHBOT_USER_IDS:
        return message.author.id in PATCHBOT_USER_IDS

    author_name = (message.author.name or "").lower()
    display_name = (message.author.display_name or "").lower()
    return "patchbot" in author_name or "patchbot" in display_name


@client.event
async def on_ready() -> None:
    print(f"ログイン完了: {client.user}")


@client.event
async def on_message(message: discord.Message) -> None:
    if not is_patchbot_message(message):
        return

    if TARGET_CHANNEL_IDS and message.channel.id not in TARGET_CHANNEL_IDS:
        return

    ja_url = await find_ja_patch_url(message)
    if not ja_url:
        return

    await message.reply(
        f"日本語版パッチノートはこちらです: {ja_url}",
        mention_author=False,
    )


if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN が設定されていません。")

    client.run(token)
