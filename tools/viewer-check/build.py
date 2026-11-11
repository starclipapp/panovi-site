"""本物の index.html から「体験する」のビューアだけを抜き、
   押したあとの状態を測れる検査ページを作る。
   ★ページを直したら ./_xp/build.py を走らせて測り直すこと。"""
import re, pathlib, shutil
root = pathlib.Path(__file__).resolve().parents[2]
src = (root/"index.html").read_text(encoding="utf-8")
body = re.search(r'<div class="col xp rise" id="xp".*?</div>\s*</section>', src, re.S).group(0)
body = body.rsplit("</section>", 1)[0].replace('class="col xp rise"', 'class="col xp"')
css  = re.search(r"<style>(.*?)</style>", src, re.S).group(1)
out  = pathlib.Path(__file__).resolve().parent/"page"
out.mkdir(exist_ok=True)
(out/"index.html").write_text(
    '<!doctype html><meta charset="utf-8"><title>xp harness</title>\n<style>' + css +
    '\nbody{background:#04201f;margin:0;padding:20px}\n'
    '#log{position:fixed;left:8px;top:8px;z-index:99;background:#000c;color:#0f9;'
    'font:12px monospace;padding:8px;white-space:pre}\n</style>\n'
    '<div id="log">起動</div>\n' + body +
    '\n<script>window.onerror=(m,s,l)=>{document.getElementById("log").textContent="JSエラー: "+m+" @"+l};</script>'
    '\n<script src="viewer.js"></script>\n<script src="probe.js"></script>\n', encoding="utf-8")
out.mkdir(exist_ok=True)
shutil.copy(root/"viewer.js", out/"viewer.js")
shutil.copy(pathlib.Path(__file__).resolve().parent/"probe.js", out/"probe.js")
(out/"img").mkdir(exist_ok=True)
for n in ["viewer.mp4","viewer_4k.mp4","viewer_poster.jpg"]:
    shutil.copy(root/"img"/n, out/"img"/n)
print("作った:", out/"index.html")
