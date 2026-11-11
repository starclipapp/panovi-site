/* 押したあとに本当に見えているかを測る。
   ★「覆えている」= 映像が台(16:9)を埋めていて黒が出ない状態。
     『全体』だけは意図して上下に黒が出るので、そこだけ別扱い。 */
const L = document.getElementById('log');
const xp = document.getElementById('xp');
const v = xp.querySelector('video');
const film = xp.querySelector('.xp-film');
const st = xp.querySelector('.xp-stage');
const out = [];

/// 台の**中身の枠**（1pxの枠線を除いた内側）。枠線まで入れると
/// 「左端に寄せた」ときに枠線のぶん1pxずれて、いつも不合格になる。
function inner() {
  const r = st.getBoundingClientRect();
  return { left: r.left + st.clientLeft, top: r.top + st.clientTop,
           right: r.left + st.clientLeft + st.clientWidth,
           bottom: r.top + st.clientTop + st.clientHeight };
}
function covered() {
  const r = inner(), f = film.getBoundingClientRect();
  return (f.left - r.left) <= 0.5 && (f.right - r.right) >= -0.5
      && (f.top - r.top) <= 0.5 && (f.bottom - r.bottom) >= -0.5;
}
function posterShown() {
  return getComputedStyle(xp.querySelector('.xp-poster')).display !== 'none';
}
function check(name, expectCovered) {
  const r = inner(), f = film.getBoundingClientRect();
  const ok = covered() === expectCovered;
  out.push((ok ? '○ ' : '✘ ') + name + ' 覆=' + covered()
    + ' L' + Math.round(f.left - r.left) + ' R' + Math.round(f.right - r.right)
    + ' T' + Math.round(f.top - r.top) + ' B' + Math.round(f.bottom - r.bottom)
    + ' w' + Math.round(f.width));
  L.textContent = out.join('\n');
}

out.push('押す前 ポスター=' + posterShown());
xp.querySelector('[data-act="start"]').click();
out.push('押した直後 ポスター=' + posterShown() + '（読み込み中も黒くしない）');

setTimeout(() => {
  out.push('--- 読み込み後 video=' + v.videoWidth + 'x' + v.videoHeight + ' ---');
  check('はじめの見え方', true);
  xp.querySelector('[data-frame="left"]').click();   check('左', true);
  xp.querySelector('[data-frame="right"]').click();  check('右', true);
  xp.querySelector('[data-frame="center"]').click(); check('中央', true);
  xp.querySelector('[data-zoom-by="1.5"]').click();  check('寄る', true);
  xp.querySelector('[data-zoom-by="0.6667"]').click(); check('引く', true);
  xp.querySelector('[data-act="whole"]').click();    check('全体(黒が出るのが正しい)', false);
  xp.querySelector('[data-act="reset"]').click();    check('最初に戻す', true);
  out.push(out.some(l => l.startsWith('✘')) ? '★赤あり' : 'すべて○');
  L.textContent = out.join('\n');
}, 4000);
