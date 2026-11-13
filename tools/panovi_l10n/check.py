"""panovi サイトの多言語ページを検査する。

    python3 tools/panovi_l10n/check.py

  1. pt / es のページに日本語の文字が0(言語切替の <a lang="ja">日本語</a> だけは例外)
  2. 全ページの src / href / poster / data-src / data-fallback / import の参照先がリポジトリに実在する
     (外部URLは除く)。ページ内リンク(#id)は、その id がページにあるか
  3. pt / es に英語版と同じ文(=訳し漏れ)が残っていないか
  4. 4言語の hreflang がそろっているか
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
import langs as L  # noqa: E402
from build import JP, JA_LINK  # noqa: E402

PAGES = {
    "main": ["index.html", "en/index.html", "pt/index.html", "es/index.html"],
    "privacy": ["privacy/index.html", "en/privacy/index.html",
                "pt/privacy/index.html", "es/privacy/index.html"],
    "viewer": ["viewer/index.html", "viewer/en/index.html",
               "viewer/pt/index.html", "viewer/es/index.html"],
    "guide": ["viewer/guide.html", "viewer/en/guide.html",
              "viewer/pt/guide.html", "viewer/es/guide.html"],
}
NEW = [p for ps in PAGES.values() for p in ps if "/pt/" in p or "/es/" in p]

# 訳さなくてよい(どの言語でも同じ)もの
SAME_OK = {
    "panovi", "App Store", "FAQ", "4K × 2", "1.0×", "Zoom +", "© 2026 starclip", "panovi viewer",
    "JA", "EN", "PT", "ES", "日本語", "English", "Português", "Español", "100%", "ZOOM",
    "2×", "−10", "+10", "▶", "?", "×", "✕", "⚙", "→", "01", "02", "03", "Bluetooth", "YouTube",
    "Zoom", "K", "J", "L", "M", "F", "R", "Shift", "←", "→", "↑", "↓", "−", "+", "0–9", "0", "9",
    "–", "▶ YouTube", "◼", "https://www.youtube.com/watch?v=…", "https://youtu.be/…",
    "https://www.youtube.com/shorts/…", "https://example.com/movie.mp4", "https://www.youtube.com/watch?v=…",
    "2 iPhones", "© 2026 panovi —", "VR", "8K", "Centro", "·", "|", "/", "(", ")", ".", ":", "—",
}
ATTRS = ("alt", "aria-label", "title", "placeholder", "content", "data-label-play",
         "data-label-pause", "data-fallback-note")


class Grab(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs, self.ids, self.texts, self.hreflang = [], set(), [], {}
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style"):
            self._skip += 1
            if tag == "script" and a.get("src"):
                self.refs.append(a["src"])
        for k in ("href", "src", "poster", "data-src", "data-fallback"):
            if a.get(k) and not (tag == "script" and k == "src"):
                self.refs.append(a[k])
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "link" and a.get("rel") == "alternate" and a.get("hreflang"):
            self.hreflang[a["hreflang"]] = a["href"]
        for k in ATTRS:
            if a.get(k) and not (tag == "meta" and a.get("name") in ("viewport", "theme-color")) \
                    and not (tag == "meta" and k == "content" and a.get("property") == "og:image"):
                self.texts.append(a[k].strip())

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip and data.strip():
            self.texts.append(" ".join(data.split()))


def grab(path):
    g = Grab()
    src = (REPO / path).read_text(encoding="utf-8")
    g.feed(src)
    # モジュールの import も参照として数える
    for m in re.finditer(r"""import\s[^'"]*?from\s+['"]([^'"]+)['"]""", src):
        g.refs.append(m.group(1))
    return g, src


def resolve(page, ref):
    u = urlsplit(ref)
    if u.scheme or ref.startswith("//"):
        return None
    if not u.path:
        return ("#", u.fragment)
    base = REPO if u.path.startswith("/") else (REPO / page).parent
    target = (base / unquote(u.path).lstrip("/")).resolve() if u.path.startswith("/") else (base / unquote(u.path)).resolve()
    if u.path.endswith("/") or target.is_dir():
        target = target / "index.html"
    return ("file", target)


def main():
    bad = 0
    print("== 1. 日本語の文字(pt/es) ==")
    for p in NEW:
        src = (REPO / p).read_text(encoding="utf-8")
        n = len(JP.findall(JA_LINK.sub("", src)))
        allowed = len(JA_LINK.findall(src))
        print(f"  {p}: 日本語 {n} 文字 (言語切替の『日本語』リンク {allowed} 個は除外)")
        bad += n > 0

    print("== 2. 参照先の実在 ==")
    total = 0
    for kind, ps in PAGES.items():
        for p in ps:
            g, _ = grab(p)
            for ref in g.refs:
                r = resolve(p, ref)
                if r is None:
                    continue
                total += 1
                if r[0] == "#":
                    if r[1] and r[1] not in g.ids:
                        print(f"  NG {p}: ページ内リンク #{r[1]} の id が無い")
                        bad += "/pt/" in p or "/es/" in p
                elif not r[1].exists():
                    print(f"  NG {p}: {ref} -> {r[1]} が無い")
                    bad += 1
    print(f"  ローカル参照 {total} 件を確認")

    print("== 3. 訳し漏れ(英語版と同じ文) ==")
    for kind, ps in PAGES.items():
        en, _ = grab(ps[1])
        en_texts = set(en.texts)
        for p in ps[2:]:
            g, _ = grab(p)
            left = [t for t in g.texts if t in en_texts and t not in SAME_OK and not re.fullmatch(r"[\d\s×.%:/–—-]+", t)]
            print(f"  {p}: 英語版と同じ文 {len(left)} 件" + (f" -> {left}" if left else ""))

    print("== 4. hreflang ==")
    for kind, ps in PAGES.items():
        want = {c: L.SITE + L.PAGES[kind][c] for c, _, _ in L.LANGS}
        want["x-default"] = L.SITE + L.PAGES[kind][L.X_DEFAULT]
        for p in ps:
            g, _ = grab(p)
            ok = g.hreflang == want
            print(f"  {'OK' if ok else 'NG'} {p}: {sorted(g.hreflang)}")
            bad += not ok
            for code, url in g.hreflang.items():
                local = REPO / urlsplit(url).path.lstrip("/")
                if local.is_dir():
                    local = local / "index.html"
                if not local.exists():
                    print(f"    NG hreflang {code} -> {url} が無い")
                    bad += 1

    print("合格" if not bad else f"不合格 {bad} 件")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
