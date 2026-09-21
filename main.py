import os
import requests
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

BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
CHANNEL_ID = os.environ.get("DISCORD_CHANNEL_ID")
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def send_discord_notification(message):
    data = {"content": message}
    try:
        requests.post(WEBHOOK_URL, json=data, timeout=10)
    except Exception as e:
        print(f"Discord通知エラー: {e}")

def get_latest_user_message():
    """ボット以外のユーザーが送信した最新のメッセージを取得する"""
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit=10"
    headers = {"Authorization": f"Bot {BOT_TOKEN}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            messages = response.json()
            for msg in messages:
                # ボット自身のメッセージ（author.botがTrue）はスキップして、人間のメッセージを探す
                if not msg.get("author", {}).get("bot", False):
                    return msg["content"].strip()
    except Exception as e:
        print(f"Discordからのメッセージ取得エラー: {e}")
    return None

def main():
    content = get_latest_user_message()
    if not content:
        print("Discordから有効なユーザーメッセージを取得できませんでした。")
        return

    print(f"取得したユーザーメッセージ: {content}")

    parts = content.split()
    is_search = False
    query = content

    if len(parts) == 2 and parts[1].isdigit():
        is_search = False
    elif content.isdigit():
        is_search = False
    elif content in STORE_URLS:
        is_search = False
    else:
        is_search = True

    # --- 買取先検索モード ---
    if is_search:
        print(f"買取先検索モード: 「{query}」")
        found_store = "該当する館が見つかりませんでした（名称を確認してください）"
        
        for key, store in KAITORI_DATABASE.items():
            if key in query:
                found_store = store
                break
        
        msg = f"🔍 **【K-BOOKS売却先検索】**\n入力キーワード: **{query}**\nおすすめの売却先: **{found_store}**"
        send_discord_notification(msg)
        print("検索結果を通知しました。")
        return

    # --- 番号監視モード ---
    if len(parts) >= 2 and parts[1].isdigit():
        store_name = parts[0]
        my_number = int(parts[1])
    elif content.isdigit():
        store_name = DEFAULT_STORE
        my_number = int(content)
    else:
        print("有効なコマンドとして認識されませんでした。")
        return

    target_url = STORE_URLS.get(store_name)
    if not target_url:
        print(f"未知の店舗名です: {store_name}")
        return

    print(f"監視対象 -> 店舗: {store_name} / 番号: {my_number}")

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(target_url, headers=headers, timeout=10)
        response.encoding = response.apparent_encoding
    except Exception as e:
        print(f"ページ取得エラー: {e}")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    contents_area = soup.find('div', class_='contents-area')
    current_status = contents_area.find('p').get_text(strip=True) if contents_area and contents_area.find('p') else ""

    print(f"現在のサイト状況: {current_status}")

    if "準備中" in current_status:
        print("まだ呼び出しが始まっていません（準備中）。")
        return

    if current_status.isdigit():
        current_num = int(current_status)
        if current_num >= my_number:
            msg = f"@here 🎯 【{store_name}】の順番が来ました！\n設定番号: **{my_number}** / 現在の呼び出し番号: **{current_num}**\n{target_url}"
            send_discord_notification(msg)
            print("通知を送信しました。")
        else:
            print(f"まだ {store_name} の自分の番号（{my_number}）には達していません（現在 {current_num} 番）。")

if __name__ == "__main__":
    main()
