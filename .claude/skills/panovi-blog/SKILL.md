---
name: panovi-blog
description: panovi の使いかたブログの次の記事を書く（日本語の原稿 → 英・葡・西の訳 → 予約 → 検査）。「次のブログ」「記事を書いて」「ブログを予約」「新機能の記事」などで使う。引数に slug や題を渡せる。
---

# panovi ブログの記事を1本仕上げる

まず `content/blog/README.md`（書き方と決まり）と `content/blog/CALENDAR.md`（予定と材料）を読む。

1. **題を決める**。引数があればそれ。無ければ CALENDAR.md で「未着手」のいちばん早い行。
   「リリース確認待ち」の行は、ユーザーにリリース済みか確かめてから書く（未リリースなら `draft: yes`）。
2. **事実を確かめる**。書く機能がアプリに本当にあるかを `../Panovi` のコード・
   `../MultiCamVideoRecPJ/tools/store_metadata/ja.json`・`../Panovi/docs/訴求と見せ方.md` §5 で確かめる。
   存在しない機能・言えない表現（「8Kで撮れる」など）・価格の額・競合名は書かない。
3. **ボタン名を拾う**。`../Panovi/Panovi/Localizable.xcstrings` から、記事に出す画面の言葉の
   ja / en / pt-BR / es を引いておく（訳ではアプリの訳をそのまま使う）。
4. **`ja.md` を書く**。既存の記事（`content/blog/first-video/ja.md` など）と同じ口調・長さ。
   リードで「誰の・どんな場面に効くか」を言い、見出しは具体的に。最後は「次に読む」と `{{appstore}}`。
   リンクは `post:` `home:#` `viewer:` を使う。
   問いに答える記事は、リードで結論を言い切り、比較は表にし、最後に「## よくある質問」（各言語の決まった見出し。README 参照）と ### の問いを置く。frontmatter の keywords に、その言語で実際に検索される言い回しを入れる。
   `description` とリードには検索語（パノラマ動画／パノラマビデオ・場面の言葉）を自然に1回入れる。訳でも各言語の検索語（panoramic video / vídeo panorâmico / video panorámico）を入れる。
5. **`meta.txt`** を書く。date は CALENDAR.md の日付（過去の日付なら次の金曜）。image はサイトにある画像。
6. **訳す**。en / pt（ブラジル）/ es（中南米・tú）。見出し・画像・`{{appstore}}` の数は日本語と同じに。
   言葉づかいは各言語のトップページ（`en/index.html` `pt/index.html` `es/index.html`）に合わせる。
7. **確かめる**。`sh tools/build_site.sh` が通ること。予約記事は
   `python3 tools/blog/build.py --preview <scratchpad>/preview` で作って見た目も確かめる。
8. CALENDAR.md の状態を「予約済み（4言語）」にする。commit はユーザーに聞いてから。

書き終えたら、題・公開日・確かめられなかった事実（あれば）を短く報告する。
