#!/bin/sh
# サイトの生成物をすべて作り直して検査する。push の前と、毎朝の自動公開で使う。
#   1. 英語版から pt / es を作る（tools/panovi_l10n/build.py）
#   2. ブログを作る。トップページ4言語の「使いかた・ヒント」も差し替える（tools/blog/build.py）
#   3. 多言語の検査（tools/panovi_l10n/check.py）
# ★順番が大事。1 は pt / es のトップを英語版から作り直すので、ブログの差し込みは必ずそのあと。
set -eu
cd "$(dirname "$0")/.."
python3 tools/panovi_l10n/build.py > /dev/null
python3 tools/blog/build.py "$@"
python3 tools/panovi_l10n/check.py > /dev/null && echo "検査: 合格"
