# k-books-checker

K-BOOKS の買取呼び出し番号を監視して、順番が近づいたら Discord で知らせる Bot です。
常駐型なので、Discord に送ったメッセージには即座に反応し、番号は 30 秒ごとに確認します。

## 使い方（Discord で送るだけ）

| 送るメッセージ | 動き |
|---|---|
| `123` | キャラ館の 123 番を監視 |
| `同人館 123`（`同人館123` も可） | 指定した館の 123 番を監視 |
| `状況` | 自分の監視番号と、いまの呼び出し番号を表示 |
| `停止` | 自分の監視をやめる |
| `ヘルプ` | 使い方と館の名前一覧 |
| それ以外（例: `呪術廻戦`） | おすすめの売却先を検索 |

- 残り 5 番になったら「もうすぐ」、到達したら「順番が来ました」と本人にメンションします（各 1 回だけ）。
- 監視は 1 人 1 件。新しい番号を送ると上書きされます。12 時間たつと自動で終了します。
- Bot を再起動しても監視中の番号は引き継がれます（`watches.json`）。

## 構成

```
bot.py        常駐 Bot 本体（Discord 受信・30秒ごとの監視・通知）
kbooks.py     店舗URL・売却先データ・ページ/コマンドの解析
deploy/       サーバーへの設置用（setup.sh と systemd の設定）
```

以前の GitHub Actions（5分ごとの定期実行）は、実際には数時間おきにしか動かずリアルタイム性がなかったため廃止しました。

## 設置手順（Oracle Cloud の無料 VM の場合）

### 1. Discord 側の準備（初回のみ）

1. [Discord Developer Portal](https://discord.com/developers/applications) で今の Bot を開く
2. **Bot** → **Privileged Gateway Intents** の **MESSAGE CONTENT INTENT** をオンにして保存
   （これがオフだとメッセージの中身が読めず、反応しません）
3. トークンを控える（GitHub の Secrets に入れていたものと同じでOK。分からなければ Reset Token で再発行）
4. 監視させたいチャンネルを右クリック → **チャンネルIDをコピー**（開発者モードをオンにすると出ます）

### 2. 無料 VM を作る（初回のみ）

1. Oracle Cloud に登録（本人確認でカード登録が必要ですが、Always Free の範囲なら課金されません）
2. **Compute → Instances → Create instance**
   - Image: **Ubuntu**
   - Shape: **Always Free 対象**のもの（Ampere A1 か VM.Standard.E2.1.Micro）
   - SSH キーは「秘密鍵を保存」でダウンロードしておく
3. 作成後、表示される公開 IP に SSH で入る

```bash
ssh -i ダウンロードした鍵.key ubuntu@<公開IP>
```

Bot は外から接続を受けないので、ポート開放などの設定は不要です。

### 3. Bot を設置

```bash
sudo apt-get update && sudo apt-get install -y git
git clone https://github.com/test90654/k-books-checker.git
cd k-books-checker
bash deploy/setup.sh      # 1回目は .env を作って止まる
nano .env                 # トークンとチャンネルIDを書き込む（Ctrl+O で保存、Ctrl+X で終了）
bash deploy/setup.sh      # 2回目で起動＆自動起動に登録
```

Discord で `ヘルプ` と送って返事が来れば完了です。

### 更新するとき

```bash
cd ~/k-books-checker && git pull && bash deploy/setup.sh
```

### 困ったとき

```bash
sudo journalctl -u k-books-bot -f     # ログを見る（現在の呼び出し番号の変化も出ます）
sudo systemctl restart k-books-bot    # 再起動
```

## 手元で動かす場合

```bash
pip install -r requirements.txt
cp .env.example .env   # 値を書き込む
set -a; . ./.env; set +a; python bot.py
```

テスト: `pip install pytest && pytest`
