#!/bin/bash
# ページの中のビューアを「本当に押して」確かめる。
#   ./tools/viewer-check/run.sh
# 出るもの: 各操作のあとに**黒が出ていないか**（「全体」だけは出るのが正しい）。
#
# ★なぜ要るか: 2026-10-21、全体に掛けた `img,video{max-width:100%}` が
#   JS の指定した幅を縮め、押した瞬間に真っ黒になった。見た目のスクショだけでは
#   「押したあと」が写らないので気づけなかった。
set -e
cd "$(dirname "$0")/../.."
python3 tools/viewer-check/build.py
PORT=${PORT:-8777}
if ! curl -s -o /dev/null -m 2 "http://127.0.0.1:$PORT/"; then
  python3 -m http.server "$PORT" >/dev/null 2>&1 &
  SERVER=$!; sleep 1
fi
OUT=$(mktemp -d)/check.png
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --hide-scrollbars --autoplay-policy=no-user-gesture-required --window-size=1280,900 \
  --screenshot="$OUT" --virtual-time-budget=9000 \
  "http://127.0.0.1:$PORT/tools/viewer-check/page/" >/dev/null 2>&1
[ -n "$SERVER" ] && kill $SERVER 2>/dev/null || true
echo "結果の画像: $OUT  （左上の緑の文字を読む。「すべて○」なら合格）"
