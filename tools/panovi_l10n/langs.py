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


def nav(cur):
    """上の帯（PCのみ表示）。4言語の記号を並べ、今の言語に印。"""
    links = "".join(_a("main", c, short, cur) for c, _, short in LANGS)
    return f'<span class="nav-lang" role="group" aria-label="{LANG_WORD[cur]}">{links}</span>'


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
