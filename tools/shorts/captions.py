"""YouTube Shorts に重ねる文字を、4言語ぶん透明な PNG（1080×1920）にする。

    python3 tools/shorts/captions.py <作業フォルダ>

<作業フォルダ>/text/<lang>/t1.png 〜 t5.png ができる。文字は下の CAPTIONS を直す。
Chrome（headless）で HTML を写して作る（ffmpeg に文字を描く機能が入っていないため）。
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# t1: 冒頭の上の文字 / l, r: 左右の映像の名札 / t2: つながったときの文字 /
# t3, t3s: 端から端へ流すときの文字と場所 / t4: 寄るときの文字（<span class=g> は緑）/ t5a, t5b: 終わりのカード
CAPTIONS = {
    "ja": dict(t1="iPhone 2台で撮って", l="左のiPhone", r="右のiPhone", t2="1本の超ワイド動画に",
               t3="端から端まで<br>動いたまま、1本に", t3s="箱根・金時山の山頂から",
               t4="あとから<br><span class=g>見たいところへ寄れる</span>",
               t5a="iPhone 2台で、パノラマ動画", t5b="App Store で「panovi」を検索"),
    "en": dict(t1="Shot on two iPhones", l="Left iPhone", r="Right iPhone", t2="…into one ultra&#8209;wide video",
               t3="Edge to edge,<br>all in motion", t3s="From the summit of Mt. Kintoki, Hakone",
               t4="Later, zoom in<br><span class=g>wherever you like</span>",
               t5a="Panoramic video with two iPhones", t5b="Search “panovi” on the App Store"),
    "pt": dict(t1="Filmado com 2 iPhones", l="iPhone da esquerda", r="iPhone da direita", t2="…vira um só vídeo ultra&#8209;amplo",
               t3="De ponta a ponta,<br>tudo em movimento", t3s="Do topo do Monte Kintoki, em Hakone",
               t4="Depois, aproxime<br><span class=g>onde quiser</span>",
               t5a="Vídeo panorâmico com 2 iPhones", t5b="Procure “panovi” na App Store"),
    "es": dict(t1="Grabado con 2 iPhone", l="iPhone izquierdo", r="iPhone derecho", t2="…se vuelve un solo video ultra ancho",
               t3="De punta a punta,<br>todo en movimiento", t3s="Desde la cima del monte Kintoki, Hakone",
               t4="Después, acércate<br><span class=g>a donde quieras</span>",
               t5a="Video panorámico con 2 iPhone", t5b="Busca “panovi” en el App Store"),
}

CSS = """html,body{margin:0;width:1080px;height:1920px;background:transparent;overflow:hidden}
body{font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN",sans-serif;color:#fff;position:relative}
.t{position:absolute;left:0;right:0;padding:0 50px;text-align:center;font-weight:800;letter-spacing:.02em;text-wrap:balance;
   text-shadow:0 2px 14px rgba(0,0,0,.75),0 0 3px rgba(0,0,0,.6)}
.g{color:#2ef09a}"""


def pages(d):
    return {
        "t1": f'<div class="t" style="top:150px;font-size:72px">{d["t1"]}</div>',
        "t1b": f'<div class="t" style="top:262px;font-size:44px;font-weight:600;text-align:left">{d["l"]}</div>'
               f'<div class="t" style="top:932px;font-size:44px;font-weight:600;text-align:left">{d["r"]}</div>',
        "t2": f'<div class="t g" style="top:1250px;font-size:76px;line-height:1.3">{d["t2"]}</div>',
        "t3": f'<div class="t" style="top:280px;font-size:76px;line-height:1.35">{d["t3"]}</div>'
              f'<div class="t" style="bottom:300px;font-size:42px;font-weight:600">{d["t3s"]}</div>',
        "t4": f'<div class="t" style="top:300px;font-size:76px;line-height:1.35">{d["t4"]}</div>',
        "t5": '<div style="position:absolute;inset:0;background:rgba(4,20,19,.72)"></div>'
              '<img src="icon.png" style="position:absolute;left:390px;top:560px;width:300px;height:300px;border-radius:66px">'
              '<div class="t" style="top:900px;font-size:120px;letter-spacing:.04em">panovi</div>'
              f'<div class="t" style="top:1075px;font-size:50px;font-weight:700;white-space:nowrap">{d["t5a"]}</div>'
              f'<div class="t g" style="top:1200px;font-size:46px;font-weight:700;white-space:nowrap">{d["t5b"]}</div>',
    }


def main():
    work = Path(sys.argv[1] if len(sys.argv) > 1 else tempfile.gettempdir() + "/panovi-short").resolve()
    for lang, d in CAPTIONS.items():
        out = work / "text" / lang
        out.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / "img/icon.png", out / "icon.png")
        for name, body in pages(d).items():
            (out / f"{name}.html").write_text(
                f'<!doctype html><meta charset="utf-8"><style>{CSS}</style><body>{body}</body>', encoding="utf-8")
            subprocess.run([CHROME, "--headless=new", "--disable-gpu", f"--user-data-dir={tempfile.mkdtemp()}",
                            "--hide-scrollbars", "--force-device-scale-factor=1", "--default-background-color=00000000",
                            "--window-size=1080,1920", f"--screenshot={out / (name + '.png')}", (out / f"{name}.html").as_uri()],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
