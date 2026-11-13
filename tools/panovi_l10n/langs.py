"""panovi サイトの言語切替・hreflang を作る部品（ja / en / pt-BR / es）。

build.py（pt・es の生成）と、ja・en ページへの組み込みの両方がこれを使う。
言語を足すときは LANGS と PAGES に1行ずつ足す。
"""

SITE = "https://panovi.app"

# (hreflang / html lang, 自分の言語での名前, 短い記号)
LANGS = [
    ("ja", "日本語", "JA"),
    ("en", "English", "EN"),
    ("pt-BR", "Português", "PT"),
    ("es", "Español", "ES"),
]
X_DEFAULT = "en"

# ページの種類ごとの各言語のパス（サイトの根からの絶対パス）
PAGES = {
    "main": {"ja": "/", "en": "/en/", "pt-BR": "/pt/", "es": "/es/"},
    "privacy": {"ja": "/privacy/", "en": "/en/privacy/",
                "pt-BR": "/pt/privacy/", "es": "/es/privacy/"},
    "viewer": {"ja": "/viewer/", "en": "/viewer/en/",
               "pt-BR": "/viewer/pt/", "es": "/viewer/es/"},
    "guide": {"ja": "/viewer/guide.html", "en": "/viewer/en/guide.html",
              "pt-BR": "/viewer/pt/guide.html", "es": "/viewer/es/guide.html"},
}

LANG_WORD = {"ja": "言語", "en": "Language", "pt-BR": "Idioma", "es": "Idioma"}


def hreflang(kind, indent=""):
    p = PAGES[kind]
    lines = [f'{indent}<link rel="alternate" hreflang="{code}" href="{SITE}{p[code]}">'
             for code, _, _ in LANGS]
    lines.append(f'{indent}<link rel="alternate" hreflang="x-default" href="{SITE}{p[X_DEFAULT]}">')
    return "\n".join(lines)


def _a(kind, code, label, cur, extra=""):
    href = PAGES[kind][code]
    current = ' aria-current="page"' if code == cur else ""
    return f'<a href="{href}" lang="{code}" hreflang="{code}"{current}{extra}>{label}</a>'


GLOBE = ('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
         'aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.7 3.8 5.7 3.8 9s-1.3 6.3-3.8 9'
         'M12 3c-2.5 2.7-3.8 5.7-3.8 9s1.3 6.3 3.8 9"/></svg>')


def lang_menu(cur, hrefs):
    """上の帯の言語切替（プルダウン）。押すと4言語を自分の言葉で並べる。スマホでも出す。
    hrefs: 言語コード → そのページの各言語のURL。"""
    short = dict((c, s) for c, _, s in LANGS)[cur]
    links = "".join(f'<a href="{hrefs[c]}" lang="{c}" hreflang="{c}"{" aria-current=\"page\"" if c == cur else ""}>{name}</a>'
                    for c, name, _ in LANGS)
    return (f'<details class="nav-lang"><summary aria-label="{LANG_WORD[cur]}: {short}">{GLOBE}{short}</summary>'
            f'<div class="nav-lang-list">{links}</div></details>')


def nav(cur):
    """トップページの上の帯の言語切替。"""
    return lang_menu(cur, PAGES["main"])


# 言語切替の見た目と、外を押したら閉じる動き（トップ・ブログ共通）
LANG_MENU_CSS = (
    ".nav-lang{position:relative}"
    ".nav-lang summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:6px;font-size:12.5px;"
    "letter-spacing:.08em;color:var(--dim);padding:6px 11px;border-radius:999px;border:1px solid var(--rule);transition:.2s}"
    ".nav-lang summary::-webkit-details-marker{display:none}"
    ".nav-lang summary::after{content:\"\";width:5px;height:5px;border-right:1.5px solid currentColor;"
    "border-bottom:1.5px solid currentColor;transform:translateY(-2px) rotate(45deg);margin-left:2px}"
    ".nav-lang[open] summary,.nav-lang summary:hover{color:var(--paper);border-color:rgba(244,243,238,.34)}"
    ".nav-lang-list{position:absolute;right:0;top:calc(100% + 8px);min-width:160px;padding:6px;display:flex;"
    "flex-direction:column;background:#062b29;border:1px solid var(--rule);border-radius:12px;"
    "box-shadow:0 16px 44px rgba(0,0,0,.45);z-index:70}"
    ".nav-lang-list a{padding:8px 12px;border-radius:8px;font-size:14px;letter-spacing:.02em;color:var(--paper);"
    "text-decoration:none;white-space:nowrap}"
    ".nav-lang-list a:hover{background:rgba(244,243,238,.08)}"
    ".nav-lang-list a[aria-current]{color:var(--green);pointer-events:none}"
)
LANG_MENU_JS = ("<script>document.addEventListener('click',function(e){document.querySelectorAll('details.nav-lang[open]')"
                ".forEach(function(d){if(!d.contains(e.target))d.removeAttribute('open');});});</script>")


def foot(cur, kind="main"):
    """フッタ（スマホでも見える）。各言語を自分の言葉で。"""
    links = "".join(_a(kind, c, name, cur) for c, name, _ in LANGS)
    return f'<span class="foot-lang" role="group" aria-label="{LANG_WORD[cur]}">{links}</span>'


def others(kind, cur, sep=" · "):
    """今の言語以外へのリンクを区切りで並べる（プライバシー・ガイド用）。"""
    return sep.join(_a(kind, c, name, cur) for c, name, _ in LANGS if c != cur)


def viewer_menu(cur, indent="            "):
    """ビューアの上の欄。幅が狭いので、記号1つのボタン + 開くと4言語。"""
    short = dict((c, s) for c, _, s in LANGS)[cur]
    items = "\n".join(f"{indent}    " + _a("viewer", c, name, cur) for c, name, _ in LANGS)
    return (f'<details class="lang-menu">\n'
            f'{indent}  <summary class="guide-link" aria-label="{LANG_WORD[cur]}: {short}">{short}</summary>\n'
            f'{indent}  <div class="lang-menu-list">\n{items}\n{indent}  </div>\n'
            f'{indent}</details>')
