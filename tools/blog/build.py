"""panovi の使いかたブログ（4言語）を content/blog/ の原稿から作る。

    python3 tools/blog/build.py                 # 今日（日本時間）までの記事を公開する
    python3 tools/blog/build.py --today 2026-12-25   # その日になったつもりで作る
    python3 tools/blog/build.py --preview DIR   # 予約・下書きも含めて DIR に丸ごと作る（確認用）

★原稿が正。blog/ en/blog/ pt/blog/ es/blog/ と feed.xml は手で直さず、原稿を直して作り直す。
  ふだんは tools/build_site.sh から呼ぶ（多言語の生成 → ブログ → 検査の順）。

原稿の置き方（くわしくは content/blog/README.md）:
  content/blog/<slug>/meta.txt   date / category / image / order / draft
  content/blog/<slug>/ja.md en.md pt.md es.md   それぞれ title / description / image_alt と本文

予約公開: meta の date が今日（日本時間）より先の記事は作らない。
  毎朝 GitHub Actions がこれを動かすので、date を書いて push しておけばその日に出る。

作るもの:
  - 記事ページと一覧ページ（4言語）、RSS（4言語）
  - sitemap.xml の <!-- blog:start --> 〜 <!-- blog:end --> の間
  - トップページ（4言語）の <!-- blog:latest:start --> 〜 <!-- blog:latest:end --> の間（入門＋新しい2本）
"""
import argparse
import datetime as dt
import html
import re
import shutil
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
SITE_ROOT = HERE.parent.parent
CONTENT = SITE_ROOT / "content" / "blog"
sys.path.insert(0, str(HERE.parent / "panovi_l10n"))
import langs as L  # noqa: E402

SITE = L.SITE
GENERATOR = "panovi-blog"
JP = re.compile(r"[぀-ヿ㐀-鿿＀-￯　-〿]")
APPSTORE_JP = "https://apps.apple.com/jp/app/id6797261654"
APPSTORE_ANY = "https://apps.apple.com/app/id6797261654"

# 原稿のファイル名の言語 → (html lang / hreflang, サイトのパスの頭)
LANGS = {
    "ja": ("ja", "/"),
    "en": ("en", "/en/"),
    "pt": ("pt-BR", "/pt/"),
    "es": ("es", "/es/"),
}
HOME_FILE = {"ja": "index.html", "en": "en/index.html", "pt": "pt/index.html", "es": "es/index.html"}
VIEWER = {"ja": "/viewer/", "en": "/viewer/en/", "pt": "/viewer/pt/", "es": "/viewer/es/"}
VIEWER_GUIDE = {"ja": "/viewer/guide.html", "en": "/viewer/en/guide.html",
                "pt": "/viewer/pt/guide.html", "es": "/viewer/es/guide.html"}
NAMES = {code: (name, short) for code, name, short in L.LANGS}

CATEGORIES = ["start", "tips", "everyday", "sports", "news"]
CAT = {
    "start":    {"ja": "はじめて", "en": "Getting started", "pt": "Primeiros passos", "es": "Primeros pasos"},
    "tips":     {"ja": "撮影のコツ", "en": "Tips", "pt": "Dicas", "es": "Consejos"},
    "everyday": {"ja": "普段使い", "en": "Everyday", "pt": "Dia a dia", "es": "Día a día"},
    "sports":   {"ja": "スポーツ", "en": "Sports", "pt": "Esportes", "es": "Deportes"},
    "news":     {"ja": "新機能・お知らせ", "en": "What’s new", "pt": "Novidades", "es": "Novedades"},
}

# 画面の決まり文句
UI = {
    "ja": {
        "nav": "使いかた", "home": "panovi について", "blog_title": "panovi の使いかた",
        "blog_lead": "はじめての1本から、旅行やスポーツで使うコツ、新しい機能まで。panovi を使いこなすための記事をまとめています。",
        "blog_desc": "iPhone 2台でパノラマ動画（パノラマビデオ）を撮るアプリ panovi の使いかた。運動会・旅行・サッカーで使うコツや新機能のお知らせ。",
        "all": "すべて", "latest": "使いかた・ヒント", "latest_more": "記事をすべて見る",
        "latest_lead": "はじめての1本から、旅行やスポーツで使うコツまで。",
        "start_here": "まずはここから", "read": "読む",
        "cta_h": "panovi を試してみる", "cta_p": "撮影は何分でも無料。3分未満の結合はずっと無料です。",
        "cta_btn": "App Store で入手", "back": "記事の一覧へ", "feed": "RSS",
        "foot_note": "撮った映像は、あなたのiPhoneの中だけに。", "privacy": "プライバシーポリシー",
        "lang": "言語", "scheduled": "予約", "draft": "下書き",
        "suffix": "panovi パノラマ動画アプリ",
    },
    "en": {
        "nav": "Guides", "home": "About panovi", "blog_title": "panovi guides",
        "blog_lead": "From your first video to tips for travel and sports, plus what’s new. Everything you need to get the most out of panovi.",
        "blog_desc": "How to use panovi, the panoramic video app that turns two iPhones into one ultra-wide video: guides, tips for sports days, travel and soccer, and news.",
        "all": "All", "latest": "Guides & tips", "latest_more": "See all guides",
        "latest_lead": "From your first video to tips for travel and sports.",
        "start_here": "Start here", "read": "Read",
        "cta_h": "Try panovi", "cta_p": "Recording is free for any length. Stitches under 3 minutes are always free.",
        "cta_btn": "Get it on the App Store", "back": "All guides", "feed": "RSS",
        "foot_note": "Your footage stays on your iPhones.", "privacy": "Privacy Policy",
        "lang": "Language", "scheduled": "Scheduled", "draft": "Draft",
        "suffix": "panovi panoramic video app",
    },
    "pt": {
        "nav": "Guias", "home": "Sobre o panovi", "blog_title": "Guias do panovi",
        "blog_lead": "Do primeiro vídeo às dicas para viagens e esportes, além das novidades. Tudo para você aproveitar o panovi ao máximo.",
        "blog_desc": "Como usar o panovi, o app de vídeo panorâmico que transforma dois iPhones em um vídeo ultra-amplo: guias, dicas para viagens e futebol, e novidades.",
        "all": "Todos", "latest": "Guias e dicas", "latest_more": "Ver todos os guias",
        "latest_lead": "Do primeiro vídeo às dicas para viagens e esportes.",
        "start_here": "Comece por aqui", "read": "Ler",
        "cta_h": "Experimente o panovi", "cta_p": "Gravar é grátis, sem limite de tempo. Uniões com menos de 3 minutos são sempre grátis.",
        "cta_btn": "Baixar na App Store", "back": "Todos os guias", "feed": "RSS",
        "foot_note": "Suas gravações ficam só nos seus iPhones.", "privacy": "Política de Privacidade",
        "lang": "Idioma", "scheduled": "Agendado", "draft": "Rascunho",
        "suffix": "panovi, app de vídeo panorâmico",
    },
    "es": {
        "nav": "Guías", "home": "Acerca de panovi", "blog_title": "Guías de panovi",
        "blog_lead": "Desde tu primer video hasta consejos para viajes y deportes, además de las novedades. Todo para sacarle el máximo provecho a panovi.",
        "blog_desc": "Cómo usar panovi, la app de video panorámico que convierte dos iPhone en un solo video: guías, consejos para viajes y fútbol, y novedades.",
        "all": "Todos", "latest": "Guías y consejos", "latest_more": "Ver todas las guías",
        "latest_lead": "Desde tu primer video hasta consejos para viajes y deportes.",
        "start_here": "Empieza aquí", "read": "Leer",
        "cta_h": "Prueba panovi", "cta_p": "Grabar es gratis, sin límite de tiempo. Las uniones de menos de 3 minutos son siempre gratis.",
        "cta_btn": "Descargar en la App Store", "back": "Todas las guías", "feed": "RSS",
        "foot_note": "Tus grabaciones se quedan solo en tus iPhone.", "privacy": "Política de privacidad",
        "lang": "Idioma", "scheduled": "Programado", "draft": "Borrador",
        "suffix": "panovi, app de video panorámico",
    },
}
MONTHS = {
    "en": "January February March April May June July August September October November December".split(),
    "pt": "janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro".split(),
    "es": "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split(),
}


def fail(msg):
    raise SystemExit(f"[blog] {msg}")


def fmt_date(d, lang):
    if lang == "ja":
        return f"{d.year}年{d.month}月{d.day}日"
    m = MONTHS[lang][d.month - 1]
    return f"{m} {d.day}, {d.year}" if lang == "en" else f"{d.day} de {m} de {d.year}"


def blog_path(lang, slug=None):
    p = LANGS[lang][1] + "blog/"
    return p + f"{slug}/" if slug else p


def appstore(lang):
    return APPSTORE_JP if lang == "ja" else APPSTORE_ANY


def esc(s):
    return html.escape(s, quote=True)


# ───────────────────────── 原稿を読む ─────────────────────────
def read_kv(text, where):
    out = {}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            fail(f"{where}: 「key: value」の形ではない行: {line!r}")
        k, v = line.split(":", 1)
        out[k.strip()] = v.strip()
    return out


def read_md(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, flags=re.S)
    if not m:
        fail(f"{path}: 先頭に --- で囲んだ title / description / image_alt が無い")
    front = read_kv(m.group(1), path)
    for k in ("title", "description"):
        if not front.get(k):
            fail(f"{path}: {k} が空")
    return front, m.group(2)


class Post:
    def __init__(self, d):
        self.slug = d.name
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", self.slug):
            fail(f"{d}: フォルダ名は英小文字・数字・ハイフンだけにする（URLになる）")
        meta = read_kv((d / "meta.txt").read_text(encoding="utf-8"), d / "meta.txt")
        try:
            self.date = dt.date.fromisoformat(meta["date"])
        except (KeyError, ValueError):
            fail(f"{d}/meta.txt: date: 2026-11-13 の形で日付を書く")
        self.category = meta.get("category", "tips")
        if self.category not in CAT:
            fail(f"{d}/meta.txt: category は {', '.join(CATEGORIES)} のどれか")
        self.image = meta.get("image", "")
        if self.image and not (SITE_ROOT / self.image.lstrip("/")).is_file():
            fail(f"{d}/meta.txt: image のファイルが無い: {self.image}")
        self.order = int(meta.get("order", "999"))
        self.draft = meta.get("draft", "no").lower() in ("yes", "true", "1")
        self.text = {}
        missing = [lg for lg in LANGS if not (d / f"{lg}.md").is_file()]
        self.missing = missing
        for lg in LANGS:
            if lg not in missing:
                self.text[lg] = read_md(d / f"{lg}.md")

    def title(self, lg):
        return self.text[lg][0]["title"]

    def desc(self, lg):
        return self.text[lg][0]["description"]

    def alt(self, lg):
        return self.text[lg][0].get("image_alt", "")


def load_posts():
    if not CONTENT.is_dir():
        return []
    return [Post(d) for d in sorted(CONTENT.iterdir()) if d.is_dir() and (d / "meta.txt").is_file()]


# ───────────────────────── 本文（小さなMarkdown） ─────────────────────────
class Ctx:
    def __init__(self, lang, published, slug):
        self.lang = lang
        self.published = published  # 公開する slug の集合
        self.slug = slug
        self.warnings = []


def resolve(target, ctx):
    """原稿のリンク先を、その言語の実際のURLにする。公開前の記事なら None（リンクにしない）。"""
    target, _, fallback = target.partition("|")
    if target.startswith("post:"):
        slug, _, frag = target[5:].partition("#")
        if slug not in ctx.published:
            if fallback:
                return resolve(fallback, ctx)
            ctx.warnings.append(f"{ctx.slug}/{ctx.lang}: まだ公開されていない記事へのリンク {target} は文字だけにした")
            return None
        return blog_path(ctx.lang, slug) + (f"#{frag}" if frag else "")
    if target.startswith("home:"):
        return LANGS[ctx.lang][1] + target[5:]
    if target == "viewer:":
        return VIEWER[ctx.lang]
    if target == "viewer:guide":
        return VIEWER_GUIDE[ctx.lang]
    if re.match(r"https?://|/|#|mailto:", target):
        return target
    fail(f"{ctx.slug}/{ctx.lang}: 分からないリンク先 {target!r}（post:slug / home:#id / viewer: / https:// / / のどれか）")


def inline(s, ctx):
    s = esc(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)

    def link(m):
        text, target = m.group(1), html.unescape(m.group(2))
        url = resolve(target, ctx)
        if url is None:
            return text
        attrs = f' href="{esc(url)}"'
        if url.startswith("http"):
            rel = "noopener sponsored" if "amazon." in url or "link.amazon" in url else "noopener"
            attrs += f' target="_blank" rel="{rel}"'
        return f"<a{attrs}>{text}</a>"

    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, s)


def cta(lang, slug):
    u = UI[lang]
    return (f'<aside class="cta"><img src="/img/icon.png" alt="" width="56" height="56">'
            f'<div><b>{esc(u["cta_h"])}</b><p>{esc(u["cta_p"])}</p></div>'
            f'<a class="btn btn-fill" href="{appstore(lang)}" data-appstore="{esc(slug)}">{esc(u["cta_btn"])}</a></aside>')


def render_body(md, ctx):
    joiner = "" if ctx.lang == "ja" else " "
    out = []
    blocks = re.split(r"\n\s*\n", md.strip())
    for b in blocks:
        lines = b.split("\n")
        first = lines[0]
        if b.strip() == "{{appstore}}":
            out.append(cta(ctx.lang, ctx.slug))
        elif first.startswith("### "):
            out.append(f"<h3>{inline(first[4:], ctx)}</h3>")
        elif first.startswith("## "):
            out.append(f"<h2>{inline(first[3:], ctx)}</h2>")
        elif m := re.fullmatch(r'!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)', b.strip()):
            alt, src, cap = m.groups()
            if not (SITE_ROOT / src.lstrip("/")).is_file():
                fail(f"{ctx.slug}/{ctx.lang}: 画像が無い: {src}")
            fig = f'<figure><img src="{esc(src)}" alt="{esc(alt)}" loading="lazy">'
            if cap:
                fig += f"<figcaption>{inline(cap, ctx)}</figcaption>"
            out.append(fig + "</figure>")
        elif all(re.match(r"- ", ln) for ln in lines):
            # リンク1本だけの項目（「次に読む」など）は、先の記事が未公開なら項目ごと出さない
            items = [ln[2:] for ln in lines
                     if not (re.fullmatch(r"\[[^\]]+\]\(post:[^)|]+\)", ln[2:].strip())
                             and resolve(re.search(r"\((post:[^)]+)\)", ln).group(1), Ctx(ctx.lang, ctx.published, ctx.slug)) is None)]
            if items:
                out.append("<ul>" + "".join(f"<li>{inline(it, ctx)}</li>" for it in items) + "</ul>")
        elif all(re.match(r"\d+\. ", ln) for ln in lines):
            out.append("<ol>" + "".join(f"<li>{inline(re.sub(r'^\d+\. ', '', ln), ctx)}</li>" for ln in lines) + "</ol>")
        elif all(ln.startswith(">") for ln in lines):
            body = joiner.join(ln.lstrip(">").strip() for ln in lines)
            out.append(f'<div class="note"><p>{inline(body, ctx)}</p></div>')
        else:
            if any(re.match(r"(- |\d+\. |#|>)", ln) for ln in lines[1:]):
                fail(f"{ctx.slug}/{ctx.lang}: 見出し・箇条書きの前後には空行を入れる: {first[:40]!r}")
            out.append(f"<p>{inline(joiner.join(ln.strip() for ln in lines), ctx)}</p>")
    return "\n".join(out)


# ───────────────────────── 画面の部品 ─────────────────────────
CSS = """
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
:root{--ink:#04201f;--ink2:#062b29;--paper:#f4f3ee;--dim:#9fb0ac;--green:#00f994;
  --rule:rgba(244,243,238,.13);--sans:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Yu Gothic",sans-serif}
html{-webkit-text-size-adjust:100%}
body{background:var(--ink);color:var(--paper);font-family:var(--sans);line-height:1.9;
  font-feature-settings:"palt" 1;overflow-x:hidden}
img{display:block;max-width:100%;height:auto}
a{color:var(--green)}
.col{width:min(1120px,calc(100% - 40px));margin-inline:auto}
.col-n{width:min(740px,calc(100% - 40px));margin-inline:auto}
.nav{position:sticky;top:0;z-index:60;background:rgba(4,32,31,.88);backdrop-filter:blur(14px);
  -webkit-backdrop-filter:blur(14px);border-bottom:1px solid var(--rule)}
.nav-in{display:flex;align-items:center;gap:18px;height:60px}
.brand{display:flex;align-items:center;gap:10px;text-decoration:none}
.brand img{width:28px;height:28px;border-radius:7px}
.brand b{font-size:17px;font-weight:600;letter-spacing:.13em;color:var(--green)}
.nav-links{margin-left:auto;display:flex;align-items:center;gap:22px}
.nav-links a{text-decoration:none;font-size:13.5px;color:var(--dim)}
.nav-links a:hover{color:var(--paper)}
.nav-links a.btn-fill{color:#042a20}
.nav-links a[aria-current]{color:var(--paper)}
@media(max-width:640px){.nav-links .wide{display:none}}
.btn{display:inline-flex;align-items:center;justify-content:center;padding:12px 24px;border-radius:999px;
  text-decoration:none;font-size:14.5px;font-weight:700;white-space:nowrap;border:1px solid transparent}
.btn-fill{background:var(--green);color:#042a20}
.btn-line{border-color:rgba(244,243,238,.34);color:var(--paper)}
.btn-line:hover{border-color:var(--green);color:var(--green)}
.btn-sm{padding:8px 16px;font-size:13px}
.chip{display:inline-block;font-size:11.5px;letter-spacing:.08em;color:var(--green);
  border:1px solid rgba(0,249,148,.4);border-radius:999px;padding:2px 11px;line-height:1.7}
.flag{display:inline-block;font-size:11.5px;color:#042a20;background:#ffd25c;border-radius:4px;padding:1px 8px;margin-left:6px}
.meta{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px;font-size:13px;color:var(--dim)}
/* 一覧 */
.head{padding:64px 0 28px}
.head h1{font-size:clamp(30px,5vw,50px);font-weight:800;letter-spacing:-.035em;line-height:1.2}
.head p{margin-top:14px;max-width:36em;color:var(--dim);font-size:clamp(15px,1.7vw,17px)}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 30px}
.filters button{background:transparent;border:1px solid var(--rule);color:var(--paper);padding:6px 15px;
  border-radius:999px;font:inherit;font-size:13px;cursor:pointer}
.filters button[aria-pressed="true"]{background:var(--green);border-color:var(--green);color:#042a20;font-weight:700}
.cards{display:grid;gap:22px;grid-template-columns:repeat(auto-fill,minmax(min(100%,320px),1fr));padding-bottom:90px}
.card{display:flex;flex-direction:column;background:var(--ink2);border:1px solid var(--rule);border-radius:14px;
  overflow:hidden;text-decoration:none;color:inherit;transition:border-color .2s,transform .2s}
.card:hover{border-color:rgba(0,249,148,.5);transform:translateY(-2px)}
.card .pic{aspect-ratio:16/9;background:#000;overflow:hidden}
.card .pic img{width:100%;height:100%;object-fit:cover}
.card .tx{padding:18px 20px 22px;display:flex;flex-direction:column;gap:8px}
.card h2{font-size:18px;font-weight:700;line-height:1.5;letter-spacing:-.01em}
.card p{font-size:14px;color:var(--dim);line-height:1.75}
.card.big{grid-column:1/-1}
@media(min-width:860px){.card.big{flex-direction:row}.card.big .pic{flex:0 0 56%;aspect-ratio:auto;min-height:280px}
  .card.big .tx{padding:34px;justify-content:center}.card.big h2{font-size:24px}}
.card[hidden]{display:none}
/* 記事 */
.post{padding:44px 0 30px}
.crumb{font-size:13px;margin-bottom:22px}
.crumb a{color:var(--dim);text-decoration:none}
.crumb a:hover{color:var(--green)}
.post h1{margin-top:14px;font-size:clamp(27px,4.4vw,42px);font-weight:800;line-height:1.3;letter-spacing:-.03em}
.post .lead{margin-top:16px;color:var(--dim);font-size:clamp(15px,1.8vw,17px)}
.hero-img{margin:30px 0 8px;border-radius:12px;overflow:hidden;border:1px solid var(--rule)}
.prose{font-size:clamp(15.5px,1.8vw,17px)}
.prose>*+*{margin-top:1.15em}
.prose h2{margin-top:2.3em;font-size:clamp(21px,3vw,27px);font-weight:800;line-height:1.4;letter-spacing:-.02em;
  padding-top:.9em;border-top:1px solid var(--rule)}
.prose h3{margin-top:1.8em;font-size:19px;font-weight:700}
.prose p,.prose li{color:#d9e2df}
.prose strong{color:var(--paper)}
.prose ul,.prose ol{padding-left:1.3em}
.prose li+li{margin-top:.45em}
.prose li::marker{color:var(--green)}
.prose figure{margin:1.8em 0}
.prose figure img{width:100%;border-radius:10px;border:1px solid var(--rule)}
.prose figcaption{margin-top:9px;font-size:13px;color:var(--dim)}
.prose code{font-size:.9em;background:rgba(244,243,238,.08);padding:1px 6px;border-radius:4px}
.note{padding:18px 22px;border-left:2px solid var(--green);background:rgba(0,249,148,.06);border-radius:0 8px 8px 0}
.note p{color:var(--dim)}
.cta{display:flex;flex-wrap:wrap;align-items:center;gap:18px;margin:2.6em 0 0;padding:24px;
  border:1px solid rgba(0,249,148,.35);border-radius:14px;
  background:radial-gradient(120% 160% at 0% 0%,rgba(0,249,148,.12),transparent 60%)}
.cta img{width:56px;height:56px;border-radius:13px}
.cta div{flex:1 1 220px}
.cta b{font-size:18px}
.cta p{margin:4px 0 0;font-size:14px;color:var(--dim)}
.more{padding:56px 0 90px}
.more h2{font-size:20px;font-weight:800;margin-bottom:20px}
.more .cards{padding-bottom:0}
.foot{border-top:1px solid var(--rule);padding:30px 0 56px;font-size:13px;color:var(--dim);
  display:flex;flex-wrap:wrap;gap:8px 24px;align-items:center}
.foot a{color:var(--green);text-decoration:none}
.foot-lang{display:flex;flex-wrap:wrap;gap:6px 16px}
.foot a[aria-current]{color:var(--paper);pointer-events:none}
"""

GTAG = """<script async src="https://www.googletagmanager.com/gtag/js?id=G-1LM1MCM9W5"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-1LM1MCM9W5');
</script>"""

# App Store へのクリックを数える（記事ごと）。利用者を増やすのが目的なので、どの記事が効いたかを見る
CLICK_JS = """<script>
document.querySelectorAll('a[data-appstore]').forEach(function(a){
  a.addEventListener('click',function(){
    if(window.gtag)gtag('event','appstore_click',{post:a.dataset.appstore,lang:document.documentElement.lang});
  });
});
</script>"""

FILTER_JS = """<script>
(function(){
  var bs=document.querySelectorAll('.filters button'),cs=document.querySelectorAll('.cards .card');
  bs.forEach(function(b){b.addEventListener('click',function(){
    bs.forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});
    cs.forEach(function(c){c.hidden=!!b.dataset.cat&&c.dataset.cat!==b.dataset.cat;});
  });});
})();
</script>"""


def hreflang_links(paths):
    lines = [f'<link rel="alternate" hreflang="{LANGS[lg][0]}" href="{SITE}{p}">' for lg, p in paths.items()]
    lines.append(f'<link rel="alternate" hreflang="x-default" href="{SITE}{paths["en"]}">')
    return "\n".join(lines)


def lang_links(paths, cur):
    links = "".join(
        f'<a href="{p}" lang="{LANGS[lg][0]}" hreflang="{LANGS[lg][0]}"{" aria-current=\"page\"" if lg == cur else ""}>'
        f'{NAMES[LANGS[lg][0]][0]}</a>' for lg, p in paths.items())
    return f'<span class="foot-lang" role="group" aria-label="{UI[cur]["lang"]}">{links}</span>'


def page(lang, *, title, desc, path, paths, image, body, og_type="website", extra_head="", scripts=""):
    u = UI[lang]
    img = f"{SITE}{image}" if image else f"{SITE}/img/hero.jpg"
    home = LANGS[lang][1]
    privacy = {"ja": "/privacy/", "en": "/en/privacy/", "pt": "/pt/privacy/", "es": "/es/privacy/"}[lang]
    return f"""<!DOCTYPE html>
<html lang="{LANGS[lang][0]}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="generator" content="{GENERATOR}">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE}{path}">
{hreflang_links(paths)}
<link rel="alternate" type="application/rss+xml" title="{esc(u['blog_title'])}" href="{SITE}{blog_path(lang)}feed.xml">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:image" content="{img}">
<meta property="og:site_name" content="panovi">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="/img/icon.png">
<link rel="apple-touch-icon" href="/img/icon.png">
{extra_head}<style>{CSS}</style>
{GTAG}
</head>
<body>
<header class="nav">
  <div class="col nav-in">
    <a class="brand" href="{home}"><img src="/img/icon.png" alt=""><b>panovi</b></a>
    <nav class="nav-links">
      <a class="wide" href="{home}">{esc(u['home'])}</a>
      <a href="{blog_path(lang)}"{' aria-current="page"' if path == blog_path(lang) else ''}>{esc(u['nav'])}</a>
      <a class="btn btn-fill btn-sm" href="{appstore(lang)}" data-appstore="nav">App Store</a>
    </nav>
  </div>
</header>
<main>
{body}
</main>
<footer class="col foot">
  <span>© 2026 starclip</span>
  <span>{esc(u['foot_note'])}</span>
  <a href="{home}">panovi</a>
  <a href="{blog_path(lang)}feed.xml">{u['feed']}</a>
  <a href="{privacy}">{esc(u['privacy'])}</a>
  {lang_links(paths, lang)}
</footer>
{CLICK_JS}
{scripts}</body>
</html>
"""


def card(p, lang, big=False, label=None, flag=""):
    u = UI[lang]
    pic = (f'<div class="pic"><img src="{esc(p.image)}" alt="{esc(p.alt(lang))}" loading="lazy"></div>'
           if p.image else "")
    top = esc(label) if label else esc(CAT[p.category][lang])
    return (f'<a class="card{" big" if big else ""}" href="{blog_path(lang, p.slug)}" data-cat="{p.category}">{pic}'
            f'<div class="tx"><div class="meta"><span class="chip">{top}</span>'
            f'<time datetime="{p.date}">{fmt_date(p.date, lang)}</time>{flag}</div>'
            f'<h2>{esc(p.title(lang))}</h2><p>{esc(p.desc(lang))}</p></div></a>')


def status_flag(p, lang, today):
    if p.draft:
        return f'<span class="flag">{UI[lang]["draft"]}</span>'
    if p.date > today:
        return f'<span class="flag">{UI[lang]["scheduled"]}</span>'
    return ""


def json_ld(p, lang):
    import json
    d = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": p.title(lang), "description": p.desc(lang),
        "datePublished": p.date.isoformat(), "inLanguage": LANGS[lang][0],
        "mainEntityOfPage": f"{SITE}{blog_path(lang, p.slug)}",
        "author": {"@type": "Organization", "name": "starclip"},
        "publisher": {"@type": "Organization", "name": "starclip",
                      "logo": {"@type": "ImageObject", "url": f"{SITE}/img/icon.png"}},
    }
    if p.image:
        d["image"] = f"{SITE}{p.image}"
    return f'<script type="application/ld+json">{json.dumps(d, ensure_ascii=False)}</script>\n'


def article_page(p, lang, posts, published, today):
    ctx = Ctx(lang, published, p.slug)
    body_html = render_body(p.text[lang][1], ctx)
    u = UI[lang]
    # 本文の中に同じ画像があるときは、上に重ねて出さない
    hero = (f'<figure class="hero-img"><img src="{esc(p.image)}" alt="{esc(p.alt(lang))}"></figure>'
            if p.image and f'src="{esc(p.image)}"' not in body_html else "")
    # 次に読む: 同じ分類 → ほかの記事、新しい順に3本
    others = [q for q in posts if q.slug != p.slug]
    others.sort(key=lambda q: (q.category != p.category, -q.date.toordinal()))
    more = "".join(card(q, lang, flag=status_flag(q, lang, today)) for q in others[:3])
    more_html = (f'<section class="col more"><h2>{esc(u["latest"])}</h2><div class="cards">{more}</div></section>'
                 if more else "")
    body = f"""<article class="col-n post">
  <p class="crumb"><a href="{blog_path(lang)}">← {esc(u['back'])}</a></p>
  <div class="meta"><span class="chip">{esc(CAT[p.category][lang])}</span><time datetime="{p.date}">{fmt_date(p.date, lang)}</time>{status_flag(p, lang, today)}</div>
  <h1>{esc(p.title(lang))}</h1>
  {hero}
  <div class="prose">
{body_html}
  </div>
</article>
{more_html}"""
    paths = {lg: blog_path(lg, p.slug) for lg in LANGS}
    out = page(lang, title=f"{p.title(lang)} | {u['suffix']}", desc=p.desc(lang), path=paths[lang], paths=paths,
               image=p.image, body=body, og_type="article", extra_head=json_ld(p, lang))
    return out, ctx.warnings


def index_page(lang, posts, today):
    u = UI[lang]
    cats = [c for c in CATEGORIES if any(p.category == c for p in posts)]
    filters = (f'<button type="button" aria-pressed="true" data-cat="">{esc(u["all"])}</button>'
               + "".join(f'<button type="button" aria-pressed="false" data-cat="{c}">{esc(CAT[c][lang])}</button>'
                         for c in cats))
    # 「まずはここから」: はじめての記事のうち order が一番小さいもの
    starts = sorted([p for p in posts if p.category == "start"], key=lambda p: (p.order, p.date))
    first = starts[0] if starts else None
    rest = [p for p in posts if p is not first]
    cards = ""
    if first:
        cards += card(first, lang, big=True, label=u["start_here"], flag=status_flag(first, lang, today))
    cards += "".join(card(p, lang, flag=status_flag(p, lang, today)) for p in rest)
    body = f"""<section class="col head">
  <h1>{esc(u['blog_title'])}</h1>
  <p>{esc(u['blog_lead'])}</p>
</section>
<div class="col">
  <div class="filters" role="group">{filters}</div>
  <div class="cards">{cards}</div>
</div>"""
    paths = {lg: blog_path(lg) for lg in LANGS}
    return page(lang, title=f"{u['blog_title']} | {u['suffix']}", desc=u["blog_desc"], path=paths[lang], paths=paths,
                image=first.image if first else "", body=body, scripts=FILTER_JS)


def feed(lang, posts):
    u = UI[lang]
    items = []
    for p in posts[:20]:
        url = f"{SITE}{blog_path(lang, p.slug)}"
        pub = dt.datetime.combine(p.date, dt.time(9, 0), ZoneInfo("Asia/Tokyo")).strftime("%a, %d %b %Y %H:%M:%S %z")
        items.append(f"""  <item>
    <title>{esc(p.title(lang))}</title>
    <link>{url}</link>
    <guid>{url}</guid>
    <pubDate>{pub}</pubDate>
    <category>{esc(CAT[p.category][lang])}</category>
    <description>{esc(p.desc(lang))}</description>
  </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>{esc(u['blog_title'])}</title>
  <link>{SITE}{blog_path(lang)}</link>
  <description>{esc(u['blog_desc'])}</description>
  <language>{LANGS[lang][0]}</language>
{chr(10).join(items)}
</channel>
</rss>
"""


def latest_block(lang, posts):
    """トップページに差し込む「使いかた・ヒント」の節（入門1本＋新しい順に2本）。"""
    u = UI[lang]
    if not posts:
        return ""
    # 初めて来た人のために、入門（はじめての記事で order が一番小さいもの）を必ず先頭に置く
    starts = sorted([p for p in posts if p.category == "start"], key=lambda p: (p.order, p.date))
    pick = starts[:1] + [p for p in posts if p not in starts[:1]]
    items = "".join(
        f'<a class="bl-card" href="{blog_path(lang, p.slug)}"><span class="bl-cat">{esc(CAT[p.category][lang])}</span>'
        f'<b>{esc(p.title(lang))}</b></a>' for p in pick[:3])
    return f"""<section class="sec" id="guides">
  <div class="col">
    <span class="eyebrow">guides</span>
    <h2>{esc(u['latest'])}</h2>
    <p class="body">{esc(u['latest_lead'])}</p>
    <div class="bl-list">{items}</div>
    <div class="links"><a class="btn btn-line" href="{blog_path(lang)}">{esc(u['latest_more'])}</a></div>
  </div>
  <style>.bl-list{{display:grid;gap:14px;margin-top:34px;grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr))}}
  .bl-card{{display:flex;flex-direction:column;gap:8px;padding:22px 24px;border:1px solid var(--rule);border-radius:14px;
    text-decoration:none;background:var(--ink2);transition:border-color .2s}}
  .bl-card:hover{{border-color:var(--green)}}
  .bl-cat{{font-size:11.5px;letter-spacing:.08em;color:var(--green)}}
  .bl-card b{{font-size:16.5px;line-height:1.55}}</style>
</section>"""


def splice(text, start, end, new, where):
    i, j = text.find(start), text.find(end)
    if i < 0 or j < i:
        fail(f"{where}: {start} 〜 {end} の印が無い")
    return text[:i + len(start)] + "\n" + new + ("\n" if new else "") + text[j:]


def sitemap_block(posts):
    out = []
    for slug_or_none in [None] + [p.slug for p in posts]:
        paths = {lg: blog_path(lg, slug_or_none) for lg in LANGS}
        last = max(p.date for p in posts) if slug_or_none is None and posts else \
            next((p.date for p in posts if p.slug == slug_or_none), None)
        alts = "\n".join(f'    <xhtml:link rel="alternate" hreflang="{LANGS[lg][0]}" href="{SITE}{pp}"/>'
                         for lg, pp in paths.items())
        alts += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{paths["en"]}"/>'
        for lg in LANGS:
            lm = f"\n    <lastmod>{last}</lastmod>" if last else ""
            out.append(f"  <url>\n    <loc>{SITE}{paths[lg]}</loc>{lm}\n{alts}\n  </url>")
    return "\n".join(out)


# ───────────────────────── 書き出し ─────────────────────────
def write(root, rel, text, written):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")
        print("wrote", rel)
    written.add(path.resolve())


def remove_stale(root, written):
    """以前に作ったが、いまは作らない記事ページを消す（記事を消した・日付を先へ動かしたとき）。"""
    for lg in LANGS:
        base = root / blog_path(lg).lstrip("/")
        if not base.is_dir():
            continue
        for f in base.glob("*/index.html"):
            if f.resolve() not in written and f'content="{GENERATOR}"' in f.read_text(encoding="utf-8"):
                shutil.rmtree(f.parent)
                print("removed", f.parent.relative_to(root))


def check_published(p):
    if p.missing:
        fail(f"{p.slug}: 公開日を過ぎたが、{', '.join(p.missing)}.md が無い（4言語そろえてから公開する）")
    for lg in ("en", "pt", "es"):
        front, body = p.text[lg]
        s = " ".join(front.values()) + body
        if JP.search(s):
            i = JP.search(s).start()
            fail(f"{p.slug}/{lg}.md: 日本語の文字が残っている: …{s[max(0, i - 30):i + 30]}…")
    # 4言語で画像・見出しの数がそろっているか（訳し漏れ・段落の落としを見つける）
    shape = {lg: (len(re.findall(r"^## ", p.text[lg][1], flags=re.M)),
                  len(re.findall(r"^!\[", p.text[lg][1], flags=re.M)),
                  p.text[lg][1].count("{{appstore}}")) for lg in LANGS}
    if len(set(shape.values())) != 1:
        fail(f"{p.slug}: 言語によって見出し・画像・App Store の数が違う（見出し, 画像, App Store）: {shape}")


def check_links(root, written):
    """作ったページの、サイト内へのリンクと画像が実在するか（#id はトップページの id まで見る）。"""
    bad = []
    for f in sorted(written):
        if f.suffix != ".html":
            continue
        text = f.read_text(encoding="utf-8")
        for url in re.findall(r'(?:href|src)="(/[^"]*)"', text):
            path, _, frag = url.partition("#")
            path = path.split("?")[0]
            target = root / path.lstrip("/")
            if path.endswith("/"):
                target = target / "index.html"
            if not target.is_file():
                bad.append(f"{f.relative_to(root)} → {url}")
            elif frag and target.suffix == ".html" and f'id="{frag}"' not in target.read_text(encoding="utf-8"):
                bad.append(f"{f.relative_to(root)} → {url}（#{frag} が無い）")
    if bad:
        fail("リンク切れ:\n  " + "\n  ".join(bad))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", help="この日付になったつもりで作る（YYYY-MM-DD）")
    ap.add_argument("--preview", metavar="DIR", help="予約・下書きも含めて DIR にサイトを丸ごと作る")
    a = ap.parse_args()
    today = dt.date.fromisoformat(a.today) if a.today else dt.datetime.now(ZoneInfo("Asia/Tokyo")).date()

    root = SITE_ROOT
    if a.preview:
        root = Path(a.preview).resolve()
        if root == SITE_ROOT or SITE_ROOT in root.parents:
            fail("--preview はリポジトリの外のフォルダを指定する")
        if root.exists():
            shutil.rmtree(root)
        shutil.copytree(SITE_ROOT, root, ignore=shutil.ignore_patterns(".git", "content", "tools", "__pycache__"))

    all_posts = load_posts()
    if a.preview:
        posts = all_posts
    else:
        posts = [p for p in all_posts if not p.draft and p.date <= today]
    for p in posts:
        check_published(p)
    posts.sort(key=lambda p: (p.date, -p.order), reverse=True)
    published = {p.slug for p in posts}

    written, warnings = set(), []
    for lg in LANGS:
        for p in posts:
            out, w = article_page(p, lg, posts, published, today)
            warnings += w
            write(root, f"{blog_path(lg, p.slug).lstrip('/')}index.html", out, written)
        write(root, f"{blog_path(lg).lstrip('/')}index.html", index_page(lg, posts, today), written)
        write(root, f"{blog_path(lg).lstrip('/')}feed.xml", feed(lg, posts), written)
        home = root / HOME_FILE[lg]
        write(root, HOME_FILE[lg], splice(home.read_text(encoding="utf-8"), "<!-- blog:latest:start -->",
                                          "<!-- blog:latest:end -->", latest_block(lg, posts), HOME_FILE[lg]), written)
    sm = root / "sitemap.xml"
    write(root, "sitemap.xml", splice(sm.read_text(encoding="utf-8"), "<!-- blog:start -->", "<!-- blog:end -->",
                                      sitemap_block(posts), "sitemap.xml"), written)
    remove_stale(root, written)
    check_links(root, written)

    for w in sorted(set(warnings)):
        print("note:", w)
    waiting = sorted((p for p in all_posts if p.slug not in published), key=lambda p: p.date)
    print(f"公開 {len(posts)} 本（{today} 時点）" + (f"、予約・下書き {len(waiting)} 本: " +
          ", ".join(f"{p.slug}({'下書き' if p.draft else p.date})" for p in waiting) if waiting else ""))
    if a.preview:
        print(f"確認用: python3 -m http.server -d {root} 8000  →  http://localhost:8000/blog/")


if __name__ == "__main__":
    main()
