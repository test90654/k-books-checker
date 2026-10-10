"""K-BOOKS の店舗データと、サイト・コマンドの解析ロジック（ネットワークに依存しない部分）"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from bs4 import BeautifulSoup

# --- 全店舗のURLマッピング（番号監視用） ---
STORE_URLS = {
    "キャラ館プラス": "https://www.k-books.co.jp/contents/purchase/chara/callno.php",
    "同人館": "https://www.k-books.co.jp/contents/purchase/doujin/callno.php",
    "キャラ館": "https://www.k-books.co.jp/contents/purchase/anime/callno.php",
    "乙女館": "https://www.k-books.co.jp/contents/purchase/otome/callno.php",
    "キャラ館スクエア": "https://www.k-books.co.jp/contents/purchase/charasq/callno.php",
    "ライブ館プラス": "https://www.k-books.co.jp/contents/purchase/liveplus/callno.php",
    "ライブ館": "https://www.k-books.co.jp/contents/purchase/live/callno.php",
    "GAME館": "https://www.k-books.co.jp/contents/purchase/game/callno.php",
    "GAME館プラス": "https://www.k-books.co.jp/contents/purchase/gameplus/callno.php",
    "K-POP館": "https://www.k-books.co.jp/contents/purchase/kpop/callno.php",
    "動画館": "https://www.k-books.co.jp/contents/purchase/douga/callno.php",
    "ライブ館α": "https://www.k-books.co.jp/contents/purchase/livea/callno.php",
    "ファンシー館": "https://www.k-books.co.jp/contents/purchase/charaa/callno.php",
    "K-POP館プラス": "https://www.k-books.co.jp/contents/purchase/kpopplus/callno.php",
    "キャスト館": "https://www.k-books.co.jp/contents/purchase/cast/callno.php",
    "GAME館α": "https://www.k-books.co.jp/contents/purchase/gamea/callno.php",
    "アイドル館": "https://www.k-books.co.jp/contents/purchase/idol/callno.php",
    "推し活館": "https://www.k-books.co.jp/contents/purchase/oshi/callno.php",
}

# --- 買取データベース ---
KAITORI_DATABASE = {
    "鬼滅の刃": "1. キャラ館プラス（ジャンプ館）",
    "呪術廻戦": "1. キャラ館プラス（ジャンプ館）",
    "ハイキュー": "1. キャラ館プラス（ジャンプ館）",
    "テニスの王子様": "1. キャラ館プラス（ジャンプ館）",
    "僕のヒーローアカデミア": "1. キャラ館プラス（ジャンプ館）",
    "銀魂": "1. キャラ館プラス（ジャンプ館）",
    "ジョジョの奇妙な冒険": "1. キャラ館プラス（ジャンプ館）",
    "SAKAMOTO DAYS": "1. キャラ館プラス（ジャンプ館）",
    "チェンソーマン": "1. キャラ館プラス（ジャンプ館）",
    "ジャンプ系同人": "2. 同人館",
    "アニメ系同人": "2. 同人館",
    "ゲーム系同人": "2. 同人館",
    "ブルーロック": "3. キャラ館",
    "WIND BREAKER": "3. キャラ館",
    "進撃の巨人": "3. キャラ館",
    "ダイヤのA": "3. キャラ館",
    "東京リベンジャーズ": "3. キャラ館",
    "文豪ストレイドッグス": "3. キャラ館",
    "弱虫ペダル": "3. キャラ館",
    "魔入りました！入間くん": "3. キャラ館",
    "Free!": "3. キャラ館",
    "エヴァンゲリオン": "3. キャラ館",
    "コードギアス": "3. キャラ館",
    "イナズマイレブン": "3. キャラ館",
    "魔法使いの約束": "4. B1F:乙女館",
    "ブレイクマイベース": "4. B1F:乙女館",
    "スタンドマイヒーローズ": "4. B1F:乙女館",
    "オトメイト作品": "4. B1F:乙女館",
    "Rejet作品": "4. B1F:乙女館",
    "イケメンシリーズ": "4. B1F:乙女館",
    "BANANA FISH": "4. B1F:乙女館",
    "ギヴン": "4. B1F:乙女館",
    "BL作品": "4. B1F:乙女館",
    "地縛少年花子くん": "5. 1F:キャラ館スクエア",
    "黒執事": "5. 1F:キャラ館スクエア",
    "サンリオ": "5. 1F:キャラ館スクエア",
    "鋼の錬金術師": "5. 1F:キャラ館スクエア",
    "名探偵コナン": "5. 1F:キャラ館スクエア",
    "葬送のフリーレン": "5. 1F:キャラ館スクエア",
    "暁のヨナ": "5. 1F:キャラ館スクエア",
    "忍たま乱太郎": "5. 1F:キャラ館スクエア",
    "ヘタリア": "5. 1F:キャラ館スクエア",
    "アオペラ": "6. 2F:ライブ館プラス",
    "アルゴナビス": "6. 2F:ライブ館プラス",
    "A3!": "6. 2F:ライブ館プラス",
    "カリスマ": "6. 2F:ライブ館プラス",
    "ヒプノシスマイク": "6. 2F:ライブ館プラス",
    "ブラックスター": "6. 2F:ライブ館プラス",
    "Paradox Live": "6. 2F:ライブ館プラス",
    "バンドリ": "6. 2F:ライブ館プラス",
    "あんさんぶるスターズ": "7. ライブ館 / 8. GAME館",
    "うたのプリンスさまっ": "7. ライブ館",
    "アイドリッシュセブン": "7. ライブ館",
    "ツキウタ": "7. ライブ館",
    "ホロスターズ": "7. ライブ館",
    "ウマ娘": "8. 1F:GAME館",
    "スプラトゥーン": "8. 1F:GAME館",
    "ゼルダの伝説": "8. 1F:GAME館",
    "ペルソナ": "8. 1F:GAME館",
    "原神": "9. 2F:GAME館プラス",
    "ツイステッドワンダーランド": "9. 2F:GAME館プラス",
    "Fate/Grand Order": "9. 2F:GAME館プラス",
    "崩壊スターレイル": "9. 2F:GAME館プラス",
    "BTS": "10. 1F:K-POP館",
    "SEVENTEEN": "10. 1F:K-POP館",
    "Stray Kids": "10. 1F:K-POP館",
    "にじさんじ": "11. 2F:動画館",
    "浦島坂田船": "11. 2F:動画館",
    "カラフルピーチ": "11. 2F:動画館",
    "アイカツ": "12. ライブ館α",
    "プリキュア": "12. ライブ館α",
    "ちいかわ": "13. 1F:キャラ館α(ファンシー)",
    "すみっコぐらし": "13. 1F:キャラ館α(ファンシー)",
    "TWICE": "14. 2F:K-POP・J-POP館プラス",
    "LE SSERAFIM": "14. 2F:K-POP・J-POP館プラス",
    "aespa": "14. 2F:K-POP・J-POP館プラス",
    "2.5次元": "15. キャスト館",
    "プロジェクトセカイ": "16. GAME館α",
    "プロセカ": "16. GAME館α",
    "ボカロ": "16. GAME館α",
    "刀剣乱舞": "16. GAME館α",
    "Snow Man": "17. アイドル館",
    "なにわ男子": "17. アイドル館",
    "ぬいぐるみ用服": "18. 推し活館",
}

DEFAULT_STORE = "キャラ館"

STOP_WORDS = {"停止", "ストップ", "stop", "キャンセル", "cancel"}
STATUS_WORDS = {"状況", "status", "確認"}
HELP_WORDS = {"ヘルプ", "help", "使い方"}


def normalize(text: str) -> str:
    """全角数字・全角スペースなどを半角にそろえる"""
    return unicodedata.normalize("NFKC", text).strip()


@dataclass
class Command:
    kind: str  # "watch" / "stop" / "status" / "help" / "search"
    store: str | None = None
    number: int | None = None
    query: str | None = None


def parse_command(content: str) -> Command:
    text = normalize(content)
    parts = text.split()
    lower = text.lower()

    if lower in STOP_WORDS:
        return Command("stop")
    if lower in STATUS_WORDS:
        return Command("status")
    if lower in HELP_WORDS:
        return Command("help")

    if text.isdigit():
        return Command("watch", store=DEFAULT_STORE, number=int(text))
    if len(parts) == 2 and parts[1].isdigit():
        return Command("watch", store=parts[0], number=int(parts[1]))
    # 「同人館123」のように空白なしでもOK
    m = re.fullmatch(r"(\D+?)(\d+)", text)
    if m and m.group(1) in STORE_URLS:
        return Command("watch", store=m.group(1), number=int(m.group(2)))

    return Command("search", query=text)


def search_store(query: str) -> str | None:
    q = normalize(query).lower()
    for key, store in KAITORI_DATABASE.items():
        if normalize(key).lower() in q:
            return store
    return None


@dataclass
class CallStatus:
    raw: str
    number: int | None  # 現在の呼び出し番号（読めなかったら None）
    preparing: bool


def parse_call_page(html: str) -> CallStatus:
    """呼び出し番号ページから現在の番号を読み取る"""
    soup = BeautifulSoup(html, "html.parser")
    area = soup.find("div", class_="contents-area")
    raw = ""
    if area:
        p = area.find("p")
        raw = (p or area).get_text(" ", strip=True)
    raw = normalize(raw)

    if "準備中" in raw:
        return CallStatus(raw, None, True)

    nums = re.findall(r"\d+", raw)
    number = int(nums[0]) if nums else None
    return CallStatus(raw, number, False)


def decode_html(body: bytes, charset: str | None) -> str:
    for enc in [charset, "utf-8", "cp932", "euc_jp"]:
        if not enc:
            continue
        try:
            return body.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return body.decode("utf-8", errors="replace")
