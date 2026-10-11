#!/usr/bin/env bash
# サーバー上でリポジトリのフォルダから実行: bash deploy/setup.sh
# 何度実行しても大丈夫（更新時もこれを流すだけ）
set -euo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$DIR"

echo "== Python を準備"
if command -v apt-get >/dev/null; then
  sudo apt-get update -y && sudo apt-get install -y python3 python3-venv
elif command -v dnf >/dev/null; then
  sudo dnf install -y python3
fi

python3 -m venv .venv
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q

if [ ! -f .env ]; then
  cp .env.example .env
  chmod 600 .env
  echo
  echo "!! .env を作りました。トークンとチャンネルIDを書き込んでから、もう一度このスクリプトを実行してください:"
  echo "   nano $DIR/.env"
  exit 1
fi

echo "== 常駐サービスを登録"
sed -e "s#__DIR__#$DIR#g" -e "s#__USER__#$(whoami)#g" deploy/k-books-bot.service \
  | sudo tee /etc/systemd/system/k-books-bot.service >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now k-books-bot
sudo systemctl restart k-books-bot

sleep 3
sudo systemctl --no-pager status k-books-bot | head -15
echo
echo "ログを見る: sudo journalctl -u k-books-bot -f"
