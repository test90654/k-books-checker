import os
import requests
from bs4 import BeautifulSoup

# --- 全店舗のURLマッピング（番号監視用） ---
STORE_URLS = {
    "キャラ館プラス": "https://www.k-books.co.jp/contents/purchase/chara/callno.php",
    "同人館": "https://www.k-books.co.jp/contents/purchase/doujin/callno.php",
    "キャラ館": "https://www.k-books.co.jp/contents/purchase/anime/callno.php",
    "乙女館": "https://www.k-books.co.jp/contents/purchase/otome/callno.php", # B1F:乙女館
    "キャラ館スクエア": "https://www.k-books.co.jp/contents/purchase/charasq/callno.php", # 1F:キャラ館スクエア
    "ライブ館プラス": "https://www.k-books.co.jp/contents/purchase/liveplus/callno.php", # 2F:ライブ館プラス
    "ライブ館": "https://www.k-books.co.jp/contents/purchase/live/callno.php",
    "GAME館": "https://www.k-books.co.jp/contents/purchase/game/callno.php", # 1F:GAME館
    "GAME館プラス": "https://www.k-books.co.jp/contents/purchase/gameplus/callno.php", # 2F:GAME館プラス
    "K-POP館": "https://www.k-books.co.jp/contents/purchase/kpop/callno.php", # 1F:K-POP館
    "動画館": "https://www.k-books.co.jp/contents/purchase/douga/callno.php", # 2F:動画館
    "ライブ館α": "https://www.k-books.co.jp/contents/purchase/livea/callno.php",
    "ファンシー館": "https://www.k-books.co.jp/contents/purchase/charaa/callno.php", # 1F:キャラ館α(ファンシー)
    "K-POP館プラス": "https://www.k-books.co.jp/contents/purchase/kpopplus/callno.php", # 2F:K-POP・J-POP館プラス
    "キャスト館": "https://www.k-books.co.jp/contents/purchase/cast/callno.php",
    "GAME館α": "https://www.k-books.co.jp/contents/purchase/gamea/callno.php",
    "アイドル館": "https://www.k-books.co.jp/contents/purchase/idol/callno.php", # ※必要に応じてidol2等へ調整
    "推し活館": "https://www.k-books.co.jp/contents/purchase/oshi/callno.php", # ※店舗URL構造に合わせて適宜調整
}

# --- 画像内の全ジャンルを網羅した買取データベース ---
KAITORI_DATABASE = {
    # 1. キャラ館プラス (ジャンプ関連グッズ専門)
    "鬼滅の刃": "1. キャラ館プラス（ジャンプ館）",
    "呪術廻戦": "1. キャラ館プラス（ジャンプ館）",
    "ハイキュー": "1. キャラ館プラス（ジャンプ館）",
    "テニスの王子様": "1. キャラ館プラス（ジャンプ館）",
    "僕のヒーローアカデミア": "1. キャラ館プラス（ジャンプ館）",
    "銀魂": "1. キャラ館プラス（ジャンプ館）",
    "ジョジョの奇妙な冒険": "1. キャラ館プラス（ジャンプ館）",
    "SAKAMOTO DAYS": "1. キャラ館プラス（ジャンプ館）",
    "チェンソーマン": "1. キャラ館プラス（ジャンプ館）",

    # 2. 同人館 (中古女性向け同人誌全般)
    "ジャンプ系同人": "2. 同人館",
    "アニメ系同人": "2. 同人館",
    "ゲーム系同人": "2. 同人館",
    "小説系同人": "2. 同人館",
    "コミック系同人": "2. 同人館",
    "芸能系同人": "2. 同人館",

    # 3. キャラ館 (少年誌・SFアニメ・スポーツ作品等)
    "ブルーロック": "3. キャラ館",
    "WIND BREAKER": "3. キャラ館",
    "進撃の巨人": "3. キャラ館",
    "ダイヤのA": "3. キャラ館",
    "東京リベンジャーズ": "3. キャラ館",
    "文豪ストレイドッグス": "3. キャラ館",
    "弱虫ペダル": "3. キャラ館",
    "魔入りました！入間くん": "3. キャラ館",
    "Free!": "3. キャラ館",
    "真島ヒロ作品": "3. キャラ館",
    "エヴァンゲリオン": "3. キャラ館",
    "コードギアス": "3. キャラ館",
    "イナズマイレブン": "3. キャラ館",
    "ガチアクタ": "3. キャラ館",
    "メダリスト": "3. キャラ館",
    "ハンドレッドノート": "3. キャラ館",
    "とんがり帽子のアトリエ": "3. キャラ館",
    "桃源暗鬼": "3. キャラ館",

    # 4. B1F:乙女館 (乙女ゲームグッズ・BL作品グッズ等)
    "魔法使いの約束": "4. B1F:乙女館",
    "ブレイクマイベース": "4. B1F:乙女館",
    "スタンドマイヒーローズ": "4. B1F:乙女館",
    "泡沫のユークロニア": "4. B1F:乙女館",
    "Obey Me!": "4. B1F:乙女館",
    "恋と深空": "4. B1F:乙女館",
    "オトメイト作品": "4. B1F:乙女館",
    "Rejet作品": "4. B1F:乙女館",
    "イケメンシリーズ": "4. B1F:乙女館",
    "ジャックジャンヌ": "4. B1F:乙女館",
    "BANANA FISH": "4. B1F:乙女館",
    "ギヴン": "4. B1F:乙女館",
    "古道具さん": "4. B1F:乙女館",
    "和山やま": "4. B1F:乙女館",
    "BL作品": "4. B1F:乙女館",

    # 5. 1F:キャラ館スクエア (アニメ・コミック・海外アニメ系)
    "地縛少年花子くん": "5. 1F:キャラ館スクエア",
    "黒執事": "5. 1F:キャラ館スクエア",
    "サンリオ": "5. 1F:キャラ館スクエア",
    "鋼の錬金術師": "5. 1F:キャラ館スクエア",
    "ドラゴンクエスト": "5. 1F:キャラ館スクエア",
    "ファイナルファンタジー": "5. 1F:キャラ館スクエア",
    "NieR": "5. 1F:キャラ館スクエア",
    "名探偵コナン": "5. 1F:キャラ館スクエア",
    "ハリーポッター": "5. 1F:キャラ館スクエア",
    "葬送のフリーレン": "5. 1F:キャラ館スクエア",
    "星屑テレパス": "5. 1F:キャラ館スクエア",
    "桜蘭高校ホスト部": "5. 1F:キャラ館スクエア",
    "暁のヨナ": "5. 1F:キャラ館スクエア",
    "客観くんどうしちゃったの!?": "5. 1F:キャラ館スクエア",
    "忍たま乱太郎": "5. 1F:キャラ館スクエア",
    "ヘタリア": "5. 1F:キャラ館スクエア",
    "ディズニー": "5. 1F:キャラ館スクエア",
    "ハズビンホテル": "5. 1F:キャラ館スクエア",
    "時代代理人": "5. 1F:キャラ館スクエア",

    # 6. 2F:ライブ館プラス (音楽関連作品専門)
    "アオペラ": "6. 2F:ライブ館プラス",
    "アルゴナビス": "6. 2F:ライブ館プラス",
    "ALIEN STAGE": "6. 2F:ライブ館プラス",
    "A3!": "6. 2F:ライブ館プラス",
    "カリスマ": "6. 2F:ライブ館プラス",
    "クロケスタ": "6. 2F:ライブ館プラス",
    "STRANGE EDEN": "6. 2F:ライブ館プラス",
    "歌い手": "6. 2F:ライブ館プラス",
    "DIG-ROCK": "6. 2F:ライブ館プラス",
    "Paradox Live": "6. 2F:ライブ館プラス",
    "バンドリ": "6. 2F:ライブ館プラス",
    "ヒプノシスマイク": "6. 2F:ライブ館プラス",
    "フラガニアメモリーズ": "6. 2F:ライブ館プラス",
    "ブラックスター": "6. 2F:ライブ館プラス",
    "ミルグラム": "6. 2F:ライブ館プラス",
    "BOYS be MAID!": "6. 2F:ライブ館プラス",

    # 7. ライブ館 (二次元アイドル/作品関連・一部アイドル等)
    "あんさんぶるスターズ": "7. ライブ館",
    "うたのプリンスさまっ": "7. ライブ館",
    "アイドリッシュセブン": "7. ライブ館",
    "ツキウタ": "7. ライブ館",
    "ツキプロ": "7. ライブ館",
    "B-PROJECT": "7. ライブ館",
    "アイ★チュウ": "7. ライブ館",
    "華Doll": "7. ライブ館",
    "UniteUp!": "7. ライブ館",
    "アイドルマスターSideM": "7. ライブ館",
    "STATION IDOL LATCH!": "7. ライブ館",
    "VS AMBIVALENZ": "7. ライブ館",
    "HOLOSTARS": "7. ライブ館",
    "ホロスターズ": "7. ライブ館",
    "Neo-Porte": "7. ライブ館",

    # 8. 1F:GAME館 (ゲーム作品関連グッズ専門)
    "あんさんぶるスターズ": "8. 1F:GAME館", # ※重複調整
    "アイドリッシュセブン": "8. 1F:GAME館",
    "ウマ娘": "8. 1F:GAME館",
    "グノーシア": "8. 1F:GAME館",
    "大逆転裁判": "8. 1F:GAME館",
    "ストリートファイター": "8. 1F:GAME館",
    "スプラトゥーン": "8. 1F:GAME館",
    "ゼルダの伝説": "8. 1F:GAME館",
    "ダンガンロンパ": "8. 1F:GAME館",
    "デジモン": "8. 1F:GAME館",
    "Devil May Cry": "8. 1F:GAME館",
    "ペルソナ": "8. 1F:GAME館",
    "魔法少女まどかマギカ": "8. 1F:GAME館",
    "原神": "8. 1F:GAME館",
    "崩壊": "8. 1F:GAME館",

    # 9. 2F:GAME館プラス (話題のゲーム作品グッズ)
    "ツイステッドワンダーランド": "9. 2F:GAME館プラス",
    "エリオスライジングヒーローズ": "9. 2F:GAME館プラス",
    "第五人格": "9. 2F:GAME館プラス",
    "Fate/Grand Order": "9. 2F:GAME館プラス",
    "FGO": "9. 2F:GAME館プラス",
    "崩壊スターレイル": "9. 2F:GAME館プラス",
    "崩壊3rd": "9. 2F:GAME館プラス",
    "ゼンレスゾーンゼロ": "9. 2F:GAME館プラス",
    "鳴潮": "9. 2F:GAME館プラス",
    "リバース：1999": "9. 2F:GAME館プラス",

    # 10. 1F:K-POP館 (男性K-POP・グローバル男性アイドル)
    "BTS": "10. 1F:K-POP館",
    "SEVENTEEN": "10. 1F:K-POP館",
    "Stray Kids": "10. 1F:K-POP館",
    "ENHYPEN": "10. 1F:K-POP館",
    "TOMORROW X TOGETHER": "10. 1F:K-POP館",
    "NCT": "10. 1F:K-POP館",
    "ATEEZ": "10. 1F:K-POP館",
    "RIIZE": "10. 1F:K-POP館",
    "BOYNEXTDOOR": "10. 1F:K-POP館",
    "JO1": "10. 1F:K-POP館",
    "INI": "10. 1F:K-POP館",
    "DXTEEN": "10. 1F:K-POP館",
    "PLAVE": "10. 1F:K-POP館",

    # 11. 2F:動画館 (配信者関連グッズ専門店)
    "にじさんじ": "11. 2F:動画館",
    "STPR": "11. 11. 2F:動画館",
    "VOISING": "11. 2F:動画館",
    "シクフォニ": "11. 2F:動画館",
    "Element Sicks": "11. 2F:動画館",
    "浦島坂田船": "11. 2F:動画館",
    "ろこまこあこ": "11. 2F:動画館",
    "どズル社": "11. 2F:動画館",
    "TOP4": "11. 2F:動画館",
    "まじめにヤバシティ": "11. 2F:動画館",
    "めろぱか": "11. 2F:動画館",
    "カラフルピーチ": "11. 2F:動画館",
    "Crazy Raccoon": "11. 2F:動画館",
    "最俺": "11. 2F:動画館",

    # 12. ライブ館α (音楽関連作品専門店)
    "アイカツ": "12. ライブ館α",
    "プリティーシリーズ": "12. ライブ館α",
    "プリキュア": "12. ライブ館α",
    "学園アイドルマスター": "12. ライブ館α",
    "アイドルマスターシャイニーカラーズ": "12. ライブ館α",
    "おジャ魔女どれみ": "12. ライブ館α",

    # 13. 1F:キャラ館α (ファンシーグッズ専門店)
    "ちいかわ": "13. 1F:キャラ館α(ファンシー)",
    "モフサンド": "13. 1F:キャラ館α(ファンシー)",
    "サンリオ": "13. 1F:キャラ館α(ファンシー)",
    "すみっコぐらし": "13. 1F:キャラ館α(ファンシー)",
    "リラックマ": "13. 1F:キャラ館α(ファンシー)",
    "おぱんちゅうさぎ": "13. 1F:キャラ館α(ファンシー)",
    "パペットスンスン": "13. 1F:キャラ館α(ファンシー)",
    "シルバニアファミリー": "13. 1F:キャラ館α(ファンシー)",

    # 14. 2F:K-POP・J-POP館プラス (女性K-POP・女性グローバル)
    "TWICE": "14. 2F:K-POP・J-POP館プラス",
    "NiziU": "14. 2F:K-POP・J-POP館プラス",
    "ITZY": "14. 2F:K-POP・J-POP館プラス",
    "NMIXX": "14. 2F:K-POP・J-POP館プラス",
    "LE SSERAFIM": "14. 2F:K-POP・J-POP館プラス",
    "IVE": "14. 2F:K-POP・J-POP館プラス",
    "aespa": "14. 2F:K-POP・J-POP館プラス",
    "ILLIT": "14. 2F:K-POP・J-POP館プラス",

    # 15. キャスト館 (2.5次元舞台・ミュージカル)
    "2.5次元": "15. キャスト館",
    "舞台俳優": "15. キャスト館",
    "ミュージカル": "15. キャスト館",

    # 16. GAME館α (プロセカ・刀剣乱舞関連等)
    "プロジェクトセカイ": "16. GAME館α",
    "プロセカ": "16. GAME館α",
    "ボーカロイド": "16. GAME館α",
    "ボカロ": "16. GAME館α",
    "刀剣乱舞": "16. GAME館α",

    # 17. アイドル館 (STARTOTOBE・EBiDAN等)
    "Snow Man": "17. アイドル館",
    "なにわ男子": "17. アイドル館",
    "SixTONES": "17. アイドル館",
    "Travis Japan": "17. アイドル館",
    "King & Prince": "17. アイドル館",
    "EBiDAN": "17. アイドル館",

    # 18. 推し活館 (推し活アイテム専門店)
    "ぬいぐるみ用服": "18. 推し活館",
    "推し活": "18. 推し活館",
    "ロゼット": "18. 推し活館",
    "カードケース": "18. 推し活館",
    "痛バッグ": "18. 推し活館",
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

def get_latest_discord_message():
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit=1"
    headers = {"Authorization": f"Bot {BOT_TOKEN}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            messages = response.json()
            if messages:
                return messages[0]["content"].strip()
    except Exception as e:
        print(f"Discordからのメッセージ取得エラー: {e}")
    return None

def main():
    content = get_latest_discord_message()
    if not content:
        print("Discordからメッセージを取得できませんでした。")
        return

    print(f"取得したメッセージ: {content}")

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
