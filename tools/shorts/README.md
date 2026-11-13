# YouTube Shorts を作る

panovi の横長の映像から、縦の Shorts（1080×1920・約23秒）を4言語ぶん作る。
最初の1本（2026-11-14）は、サイトの金時山の映像で作った。

```sh
W=~/Movies/panovi-shorts/work                       # 作業フォルダ（どこでもよい）
mkdir -p $W
python3 tools/shorts/captions.py $W                 # 文字の画像（4言語）
for l in ja en pt es; do
  bash tools/shorts/make.sh $W $l ~/Movies/panovi-shorts/panovi-short-$l.mp4
done
```

いるもの: ffmpeg（`brew install ffmpeg`）、Google Chrome（文字を画像にするのに使う）。

## 流れ

| 秒 | 場面 | 文字（`captions.py` の CAPTIONS） |
|---|---|---|
| 0–4.5 | 左右の iPhone の映像を上下に並べる → 1本の横長に変わる | t1, l / r, t2 |
| 4.5– | 横長の映像を、縦の画面で左から右へゆっくり流す | t3, t3s（場所） |
| | 見せたいところへ寄る | t4 |
| 最後 2.5 | 終わりのカード（アイコン・App Store で検索） | t5a, t5b |

## 別の映像で作るとき

- `make.sh` の先頭の「素材と、素材ごとに決める値」を直す。`WIDE` に流す横長の映像、
  `ZOOM_CROP` に寄る場所（縦長 9:16 の切り出し。見せたいものを真ん中に）
- 文字は `captions.py` の CAPTIONS。場所の名前（t3s）は映像に合わせる
- 本番は、サイトの軽くした映像ではなく、**カメラロールにある元の結合動画**を使う（寄ったときにくっきりする）
- 人が大きく映る映像は、本人の許可があるものだけ（サッカーはトップのデモだけ許可あり）
- 曲は市販のものを使わない。YouTube の「オーディオ ライブラリ」から付ける

## 出すとき

- 題に場所と検索語、最後に `#shorts`。説明欄の1行目にその言語のブログ記事の URL
- 4言語は同じチャンネルでよい。1日ずつずらして出す。最初のコメントに記事の URL を書いて固定する
