"""K-BOOKS 呼び出し番号監視 Bot（常駐型）

Discord のメッセージを即座に受け取り、登録された番号を一定間隔で監視して、
順番が近づいた時・来た時に本人へメンションで知らせる。
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path

import aiohttp
import discord
from discord.ext import tasks

import kbooks

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("kbooks-bot")

TOKEN = os.environ["DISCORD_BOT_TOKEN"]
CHANNEL_ID = int(os.environ["DISCORD_CHANNEL_ID"]) if os.environ.get("DISCORD_CHANNEL_ID") else None
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "30"))
NOTIFY_BEFORE = int(os.environ.get("NOTIFY_BEFORE", "5"))  # 何番前に「もうすぐ」通知するか
EXPIRE_HOURS = float(os.environ.get("EXPIRE_HOURS", "12"))
STATE_FILE = Path(os.environ.get("STATE_FILE", Path(__file__).with_name("watches.json")))

HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

HELP_TEXT = (
    "📖 **使い方**\n"
    "・`123` → キャラ館の123番を監視\n"
    "・`同人館 123` → 指定した館の123番を監視\n"
    "・`状況` → 監視中の番号と現在の呼び出し番号\n"
    "・`停止` → 自分の監視をやめる\n"
    "・それ以外（例: `呪術廻戦`）→ おすすめの売却先を検索\n"
    f"館の名前: {' / '.join(kbooks.STORE_URLS)}"
)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents, allowed_mentions=discord.AllowedMentions(users=True, everyone=False))

# user_id(str) -> {store, number, channel_id, warned, created_at}
watches: dict[str, dict] = {}
last_seen: dict[str, kbooks.CallStatus] = {}
fail_counts: dict[str, int] = {}
http: aiohttp.ClientSession | None = None


# ---------- 保存 ----------
def load_state() -> None:
    global watches
    try:
        watches = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        log.info("監視 %d 件を復元しました", len(watches))
    except FileNotFoundError:
        watches = {}
    except Exception:
        log.exception("監視データの読み込みに失敗。空の状態で起動します")
        watches = {}


def save_state() -> None:
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(watches, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(STATE_FILE)


# ---------- サイト取得 ----------
async def fetch_status(store: str) -> kbooks.CallStatus:
    url = kbooks.STORE_URLS[store]
    assert http is not None
    async with http.get(url, headers=HTTP_HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
        resp.raise_for_status()
        body = await resp.read()
        html = kbooks.decode_html(body, resp.charset)
    return kbooks.parse_call_page(html)


def describe(status: kbooks.CallStatus | None) -> str:
    if status is None:
        return "未取得"
    if status.preparing:
        return "準備中"
    if status.number is None:
        return f"読み取れず（{status.raw[:30] or '空'}）"
    return f"{status.number}番"


# ---------- 監視ループ ----------
async def send(channel_id: int, text: str) -> None:
    channel = client.get_channel(channel_id) or await client.fetch_channel(channel_id)
    await channel.send(text)


@tasks.loop(seconds=POLL_SECONDS)
async def poll() -> None:
    if not watches:
        return
    now = time.time()
    changed = False

    # 期限切れ（前日の番号の消し忘れ対策）
    for uid, w in list(watches.items()):
        if now - w["created_at"] > EXPIRE_HOURS * 3600:
            del watches[uid]
            changed = True
            await send(w["channel_id"], f"<@{uid}> ⌛ {w['store']} {w['number']}番の監視は{EXPIRE_HOURS:g}時間たったので終了しました。")

    stores = sorted({w["store"] for w in watches.values()})
    results = await asyncio.gather(*(fetch_status(s) for s in stores), return_exceptions=True)

    for store, result in zip(stores, results):
        if isinstance(result, Exception):
            fail_counts[store] = fail_counts.get(store, 0) + 1
            log.warning("%s の取得に失敗 (%d回連続): %s", store, fail_counts[store], result)
            if fail_counts[store] == 10:
                for uid, w in watches.items():
                    if w["store"] == store:
                        await send(w["channel_id"], f"<@{uid}> ⚠️ {store}のページが10回続けて取得できていません。サイトを直接確認してください。\n{kbooks.STORE_URLS[store]}")
            continue

        fail_counts[store] = 0
        prev = last_seen.get(store)
        last_seen[store] = result
        if prev is None or prev.raw != result.raw:
            log.info("%s: %s", store, describe(result))
        if result.number is None:
            continue

        current = result.number
        for uid, w in list(watches.items()):
            if w["store"] != store:
                continue
            url = kbooks.STORE_URLS[store]
            if current >= w["number"]:
                await send(w["channel_id"], f"<@{uid}> 🎯 **【{store}】の順番が来ました！**\n設定番号: **{w['number']}** / 現在の呼び出し: **{current}**\n{url}")
                del watches[uid]
                changed = True
            elif not w["warned"] and w["number"] - current <= NOTIFY_BEFORE:
                await send(w["channel_id"], f"<@{uid}> ⏳ 【{store}】もうすぐです！あと **{w['number'] - current}** 番（現在 {current} / 設定 {w['number']}）")
                w["warned"] = True
                changed = True

    if changed:
        save_state()


@poll.error
async def poll_error(exc: BaseException) -> None:
    log.exception("監視ループでエラー", exc_info=exc)
    poll.restart()


# ---------- Discord イベント ----------
@client.event
async def setup_hook() -> None:
    global http
    http = aiohttp.ClientSession()
    load_state()
    poll.start()


@client.event
async def on_ready() -> None:
    log.info("ログインしました: %s（監視間隔 %d 秒）", client.user, POLL_SECONDS)


@client.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return
    if CHANNEL_ID and message.channel.id != CHANNEL_ID:
        return
    content = message.content.strip()
    if not content:
        return

    cmd = kbooks.parse_command(content)
    uid = str(message.author.id)

    if cmd.kind == "help":
        await message.reply(HELP_TEXT, mention_author=False)

    elif cmd.kind == "stop":
        w = watches.pop(uid, None)
        save_state()
        await message.reply(f"🛑 {w['store']} {w['number']}番の監視を止めました。" if w else "監視中の番号はありません。", mention_author=False)

    elif cmd.kind == "status":
        w = watches.get(uid)
        if not w:
            await message.reply("監視中の番号はありません。番号を送ると監視を始めます。", mention_author=False)
            return
        status = last_seen.get(w["store"])
        try:
            status = await fetch_status(w["store"])
            last_seen[w["store"]] = status
        except Exception as e:
            log.warning("状況確認の取得に失敗: %s", e)
        await message.reply(f"👀 監視中: **{w['store']} {w['number']}番** / 現在の呼び出し: **{describe(status)}**", mention_author=False)

    elif cmd.kind == "watch":
        if cmd.store not in kbooks.STORE_URLS:
            await message.reply(f"「{cmd.store}」という館が見つかりません。\n館の名前: {' / '.join(kbooks.STORE_URLS)}", mention_author=False)
            return
        try:
            status = await fetch_status(cmd.store)
            last_seen[cmd.store] = status
        except Exception as e:
            log.warning("登録時の取得に失敗: %s", e)
            status = None

        if status and status.number is not None and status.number >= cmd.number:
            await message.reply(f"🎯 {cmd.store}はもう **{status.number}番** まで呼ばれています！（設定 {cmd.number}番）\n{kbooks.STORE_URLS[cmd.store]}", mention_author=True)
            return

        watches[uid] = {
            "store": cmd.store,
            "number": cmd.number,
            "channel_id": message.channel.id,
            "warned": False,
            "created_at": time.time(),
        }
        save_state()
        await message.reply(
            f"✅ **{cmd.store} {cmd.number}番** の監視を始めました（{POLL_SECONDS}秒ごとに確認）。\n"
            f"現在の呼び出し: **{describe(status)}**　/　止めるときは `停止`",
            mention_author=False,
        )

    else:  # search
        found = kbooks.search_store(cmd.query or "")
        await message.reply(
            f"🔍 **【K-BOOKS売却先検索】**\n入力キーワード: **{cmd.query}**\n"
            f"おすすめの売却先: **{found or '該当する館が見つかりませんでした（名称を確認してください）'}**\n"
            "（番号の監視は `123` や `同人館 123`、使い方は `ヘルプ`）",
            mention_author=False,
        )


if __name__ == "__main__":
    client.run(TOKEN, log_handler=None)
