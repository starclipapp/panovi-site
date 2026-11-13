#!/bin/bash
# Shorts に曲を付ける。音の大きさを YouTube の基準（-14 LUFS）にそろえ、最初は少しずつ入り、最後の約2秒で小さくして終わる。
#
#   bash tools/shorts/add_music.sh <動画.mp4> <曲.mp3> <曲の何秒目から> <出力.mp4>
#
# 曲は YouTube で使ってよいものだけ（README の「曲」）。
set -euo pipefail
IN="$1"; MUSIC="$2"; START="$3"; OUT="$4"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
FADE_AT=$(python3 -c "print(max(0, $DUR - 2.2))")
ffmpeg -v error -y -i "$IN" -ss "$START" -t "$DUR" -i "$MUSIC" -filter_complex \
  "[1:a]loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=in:st=0:d=0.3,afade=t=out:st=${FADE_AT}:d=2.2,aresample=48000[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"
echo "$OUT"
