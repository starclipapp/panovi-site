#!/bin/bash
# YouTube Shorts（縦 1080×1920・約23秒）を1本作る。くわしくは README.md
#
#   python3 tools/shorts/captions.py <作業フォルダ>      # 先に文字の画像を作る
#   bash tools/shorts/make.sh <作業フォルダ> <lang> <出力.mp4>
#
# 1. 左右の iPhone の映像を上下に並べる → 1本の横長に変わる（JOIN の動画）
# 2. 横長の映像を、縦の画面で左から右へゆっくり流す（WIDE の動画）
# 3. 見せたいところへ寄る
# 4. 終わりのカード
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="$(cd "$1" && pwd)"; LANG_="$2"; OUT="$3"
T="$WORK/text/$LANG_"

# --- 素材と、素材ごとに決める値（別の映像で作るときはここを直す） ---
JOIN="$REPO/img/hero-join-mountain.mp4"   # サイトの「2本 → 1本」の動き（1920×640）
JOIN_L=896:504:24:68                       # その中の左の映像の位置（幅:高さ:x:y）
JOIN_R=896:504:1000:68                     # 右の映像
JOIN_W=1730:592:94:24                      # つながったあとの横長の映像
WIDE="$REPO/img/kintoki.mp4"               # 流す横長の映像（金時山 4008×1356）
PAN_SEC=11                                 # 流す長さ（WIDE の頭から）
ZOOM_FROM=11; ZOOM_SEC=4.7                 # 寄る場面（WIDE の何秒目から何秒）
ZOOM_CROP=762:1356:2385:0                  # 寄る前の縦長の切り出し（9:16、見せたいものを真ん中に）
ZOOM_Y=1700                                # 寄る先の高さ（切り出しを 2160×3840 にしたときの y）
ZOOM_MAX=0.6                               # どのくらい寄るか（1+この値 倍）
BG=04211f                                  # 背景の色（サイトの色）
# -----------------------------------------------------------------

X264=(-c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -r 30)
cd "$WORK"
ZOOM_N=$(python3 -c "print(round(($ZOOM_SEC-1.2)*30))")
TOTAL=$(python3 -c "print(4.5+$PAN_SEC+$ZOOM_SEC+2.5)")

ffmpeg -v error -y -i "$JOIN" -loop 1 -i "$T/t1.png" -loop 1 -i "$T/t1b.png" -loop 1 -i "$T/t2.png" -filter_complex "
color=c=0x${BG}:s=1080x1920:r=30:d=2.7[bg0];
[0:v]split=3[j0][j1][j2];
[j0]trim=0:2.7,setpts=PTS-STARTPTS,crop=${JOIN_L},scale=1080:-2:flags=lanczos[L];
[j1]trim=0:2.7,setpts=PTS-STARTPTS,crop=${JOIN_R},scale=1080:-2:flags=lanczos[R];
[bg0][L]overlay=0:330:shortest=1[s0];[s0][R]overlay=0:1000:shortest=1[stack];
color=c=0x${BG}:s=1080x1920:r=30:d=2.1[bg1];
[j2]trim=2.9:5.0,setpts=PTS-STARTPTS,crop=${JOIN_W},scale=1080:-2:flags=lanczos[W];
[bg1][W]overlay=0:(H-h)/2:shortest=1[wide];
[stack][wide]xfade=transition=fade:duration=0.3:offset=2.4[a];
[1:v]format=rgba,trim=0:4.5,fade=in:st=0.15:d=0.4:alpha=1[t1];
[2:v]format=rgba,trim=0:4.5,fade=in:st=0.15:d=0.4:alpha=1,fade=out:st=2.3:d=0.3:alpha=1[t1b];
[3:v]format=rgba,trim=0:4.5,fade=in:st=2.8:d=0.4:alpha=1[t2];
[a][t1]overlay=0:0:shortest=1[b];[b][t1b]overlay=0:0:shortest=1[c];[c][t2]overlay=0:0:shortest=1,fade=out:st=4.2:d=0.3:c=black[out]" \
  -map "[out]" -t 4.5 "${X264[@]}" s1.mp4

ffmpeg -v error -y -i "$WIDE" -loop 1 -i "$T/t3.png" -filter_complex "
[0:v]trim=0:${PAN_SEC},setpts=PTS-STARTPTS,scale=-2:1920:flags=lanczos,crop=1080:1920:x='(iw-1080)*(0.5-0.5*cos(PI*t/${PAN_SEC}))':y=0,fade=in:st=0:d=0.3:c=black[v];
[1:v]format=rgba,trim=0:${PAN_SEC},fade=in:st=0.4:d=0.5:alpha=1,fade=out:st=4.2:d=0.5:alpha=1[t];
[v][t]overlay=0:0:shortest=1[out]" -map "[out]" -t "$PAN_SEC" "${X264[@]}" s2.mp4

# 寄る場面は、文字を重ねる前の最後のコマを終わりのカードの背景に使う
ffmpeg -v error -y -i "$WIDE" -loop 1 -i "$T/t4.png" -filter_complex "
[0:v]trim=${ZOOM_FROM}:$(python3 -c "print($ZOOM_FROM+$ZOOM_SEC)"),setpts=PTS-STARTPTS,crop=${ZOOM_CROP},scale=2160:3840:flags=lanczos,
zoompan=z='1+${ZOOM_MAX}*(1-cos(PI*min(on/${ZOOM_N}\,1)))/2':x='iw/2-(iw/zoom/2)':y='${ZOOM_Y}-(${ZOOM_Y}/zoom)':d=1:s=1080x1920:fps=30[v];
[1:v]format=rgba,trim=0:${ZOOM_SEC},fade=in:st=0.5:d=0.5:alpha=1[t];
[v]split[v1][v2];[v2]trim=$(python3 -c "print($ZOOM_SEC-0.1)"):${ZOOM_SEC},setpts=PTS-STARTPTS[lastf];[v1][t]overlay=0:0:shortest=1[out]" \
  -map "[out]" -t "$ZOOM_SEC" "${X264[@]}" s3.mp4 -map "[lastf]" -update 1 -frames:v 1 last.png

ffmpeg -v error -y -loop 1 -i last.png -loop 1 -i "$T/t5.png" -filter_complex "
[0:v]boxblur=20:2,format=rgba[b];[1:v]format=rgba,fade=in:st=0:d=0.5:alpha=1[t];[b][t]overlay=0:0,trim=0:2.5[out]" \
  -map "[out]" -t 2.5 "${X264[@]}" s4.mp4

# 音は無し（YouTube の編集画面で、オーディオ ライブラリの曲を付けられる）
ffmpeg -v error -y -i s1.mp4 -i s2.mp4 -i s3.mp4 -i s4.mp4 -f lavfi -t "$TOTAL" -i anullsrc=r=48000:cl=stereo \
  -filter_complex "[0:v][1:v][2:v][3:v]concat=n=4:v=1:a=0[v]" -map "[v]" -map 4:a "${X264[@]}" -c:a aac -b:a 128k \
  -shortest -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height -of csv=p=0 "$OUT" | tr '\n' ' '; echo " $OUT"
