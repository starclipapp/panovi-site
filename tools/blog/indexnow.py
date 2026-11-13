"""変わったページを IndexNow（Bing・Yandex など）に知らせる。GitHub Actions が公開のあとに呼ぶ。

    python3 tools/blog/indexnow.py <git の比較元> [<比較先 = HEAD>]

その間に変わった HTML のうち、サイトマップに載るページ（トップ・ブログ・FAQ）のURLだけを送る。
鍵はサイトの直下の <鍵>.txt（中身も鍵）。Google は IndexNow を使わない（Search Console で頼む）。
"""
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

SITE_HOST = "panovi.app"
KEY = "662ad7fa50aaab584062a302cd3acb40"
ROOT = Path(__file__).resolve().parent.parent.parent


def changed(base, head):
    out = subprocess.run(["git", "diff", "--name-only", base, head], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout.split()
    urls = []
    for f in out:
        if not f.endswith("index.html") or f.startswith(("20/", "archive_", "tools/", "content/", "pricing/")):
            continue
        if not (ROOT / f).exists():
            continue
        path = "/" + f[: -len("index.html")]
        urls.append(f"https://{SITE_HOST}{path}")
    return sorted(set(urls))


def main():
    if len(sys.argv) < 2 or set(sys.argv[1]) <= {"0"}:
        print("比較元が無いので送らない")
        return
    urls = changed(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "HEAD")
    if not urls:
        print("変わったページなし")
        return
    body = json.dumps({"host": SITE_HOST, "key": KEY, "keyLocation": f"https://{SITE_HOST}/{KEY}.txt",
                       "urlList": urls[:10000]}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("IndexNow", r.status, len(urls), "件:", *urls, sep="\n  ")
    except Exception as e:  # 知らせるのに失敗しても公開は止めない
        print("IndexNow に送れなかった:", e)


if __name__ == "__main__":
    main()
