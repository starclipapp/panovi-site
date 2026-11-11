/* panovi 体験ビューア
   横長の結合映像を 16:9 に切り出し、ドラッグとピンチで見たいところへ寄るだけの部品。
   外部ライブラリなし。<video> に CSS transform を掛けている。

   ★最初の見え方は HTML の data 属性で決める（#xp）:
       data-zoom  … 始めの倍率。1.0 = 高さいっぱい（黒は出ない）
       data-cx/cy … 始めに画面中央へ置く点（映像の中での割合 0〜1）
     既定を「高さいっぱいの中央」にすると、**空と手前の空いた地面ばかり**が映り、
     選手は上の方に小さく出る。だから少し寄せて、人のいる高さへ合わせる。 */
(function () {
  const root = document.getElementById('xp');
  if (!root) return;
  const stage   = root.querySelector('.xp-stage');
  const film    = root.querySelector('.xp-film');
  const video   = root.querySelector('video');
  const hint    = root.querySelector('.xp-hint');
  const note    = root.querySelector('.xp-note');
  const readout = root.querySelector('.xp-zoom');
  const outBtn  = root.querySelector('[data-act="out"]');
  const barPlay = root.querySelector('.xp-bar [data-act="play"]');
  // 実行中に書き換える文言は HTML 側の data 属性から読む（日本語ページは属性なし＝従来どおり）。
  //   en/pt/es ページ: #xp に data-fallback-note、再生ボタンに data-label-play / data-label-pause
  const L = {
    play:  (barPlay && barPlay.dataset.labelPlay)  || '再生',
    pause: (barPlay && barPlay.dataset.labelPause) || '一時停止',
    fallback: root.dataset.fallbackNote || 'この端末では原寸を再生できないため、少し小さい版に切り替えました。',
  };
  // ページごとに上限を指定。未指定の旧デモでは、従来どおり 1 倍を維持する。
  const configuredMax = Number(root.dataset.maxZoom);
  const MAX = Number.isFinite(configuredMax) && configuredMax >= 1 ? configuredMax : 1;

  const startZoom = parseFloat(root.dataset.zoom || '1') || 1;
  const startCX   = parseFloat(root.dataset.cx || '0.5');
  const startCY   = parseFloat(root.dataset.cy || '0.5');

  let AR = parseFloat(root.dataset.ar || '') || 6060 / 1496;  // 読み込めたら実寸で上書き
  let baseW = 0, baseH = 0, minS = 1, s = startZoom, tx = 0, ty = 0;
  let started = false;

  const stageW = () => stage.clientWidth;
  const stageH = () => stage.clientHeight;

  function sizes() {
    const h = stageH();
    baseH = h; baseW = h * AR;
    // ★一番引いた状態＝全体が横に収まるところ。ここだけは上下に黒が出るが、
    //   **人が「全体」を押したときだけ**（既定にはしない）。
    minS = Math.min(1, stageW() / baseW);
    video.style.width = baseW + 'px';
    video.style.height = baseH + 'px';
  }
  function clamp() {
    const w = stageW(), h = stageH(), vw = baseW * s, vh = baseH * s;
    tx = vw <= w ? (w - vw) / 2 : Math.min(0, Math.max(w - vw, tx));
    ty = vh <= h ? (h - vh) / 2 : Math.min(0, Math.max(h - vh, ty));
  }
  function apply() {
    film.style.transform = `translate3d(${tx}px,${ty}px,0) scale(${s})`;
    if (readout) readout.textContent = s.toFixed(1) + '×';
    if (outBtn) outBtn.disabled = s <= minS + 0.001;
  }
  /// 映像の中の (cx,cy) を画面の真ん中に置く。
  function center(cx, cy) {
    tx = stageW() / 2 - cx * baseW * s;
    ty = stageH() / 2 - cy * baseH * s;
    clamp(); apply();
  }
  function reset() { s = Math.max(minS, startZoom); sizes(); center(startCX, startCY); }

  function layout(keep) {
    if (!stageW() || !stageH()) return;
    const cx = baseW ? (stageW() / 2 - tx) / (baseW * s) : startCX;
    const cy = baseH ? (stageH() / 2 - ty) / (baseH * s) : startCY;
    sizes();
    s = Math.max(minS, Math.min(MAX, s));
    if (keep) center(cx, cy); else center(startCX, startCY);
  }
  function zoomAt(ns, px, py) {
    ns = Math.max(minS, Math.min(MAX, ns));
    const k = ns / s;
    tx = px - (px - tx) * k; ty = py - (py - ty) * k; s = ns;
    clamp(); apply();
  }
  function frame(where) {
    const w = stageW(), vw = baseW * s;
    tx = where === 'left' ? 0 : where === 'right' ? w - vw : (w - vw) / 2;
    clamp(); apply();
  }
  function whole() { s = minS; sizes(); center(0.5, 0.5); }
  function hideHint() { hint && hint.classList.add('is-gone'); }

  // 重い動画なので、押されるまで読み込まない
  function begin() {
    if (started) return;
    started = true;
    root.classList.add('is-live');
    if (!video.src && video.dataset.src) video.src = video.dataset.src;
    video.play().catch(() => {});
    setTimeout(hideHint, 6000);
  }
  function toggle() { video.paused ? video.play().catch(() => {}) : video.pause(); }

  video.addEventListener('loadedmetadata', () => {
    if (video.videoWidth) AR = video.videoWidth / video.videoHeight;
    reset();
  });
  // ★**最初の絵が出てから**ポスターを外す。でないと読み込みのあいだ真っ黒になる。
  const ready = () => { root.classList.add('is-ready'); reset(); };
  video.addEventListener('loadeddata', ready);
  video.addEventListener('playing', ready);
  // 横に長すぎて再生できない端末向けの控え
  video.addEventListener('error', () => {
    const alt = video.dataset.fallback;
    if (alt && video.src.indexOf(alt) < 0) {
      video.src = alt;
      if (note) note.textContent = L.fallback;
      video.play().catch(() => {});
    }
  });
  video.addEventListener('play',  () => { if (barPlay) barPlay.textContent = L.pause; });
  video.addEventListener('pause', () => { if (barPlay) barPlay.textContent = L.play; });

  // 指とマウス
  let drag = null;
  stage.addEventListener('pointerdown', (e) => {
    if (!started) { begin(); return; }
    stage.setPointerCapture(e.pointerId);
    drag = { x: e.clientX, y: e.clientY, tx, ty, moved: 0 };
    hideHint();
  });
  stage.addEventListener('pointermove', (e) => {
    if (!drag) return;
    const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    drag.moved = Math.max(drag.moved, Math.abs(dx) + Math.abs(dy));
    tx = drag.tx + dx; ty = drag.ty + dy; clamp(); apply();
  });
  stage.addEventListener('pointerup', () => {
    if (drag && drag.moved < 6) toggle();
    drag = null;
  });
  stage.addEventListener('pointercancel', () => { drag = null; });
  stage.addEventListener('wheel', (e) => {
    if (!started) return;
    e.preventDefault();
    const r = stage.getBoundingClientRect();
    zoomAt(s * Math.pow(1.0022, -e.deltaY), e.clientX - r.left, e.clientY - r.top);
    hideHint();
  }, { passive: false });
  // ★二度押しは**始めの見え方へ戻す**（一番引いた状態にすると上下に黒が出る）
  stage.addEventListener('dblclick', reset);

  // ボタン
  //   大きな開始ボタンは「始める」だけ。台を押した時点で begin() が走っているので、
  //   ここで toggle すると押した瞬間に止まる。
  root.querySelectorAll('[data-act="start"]').forEach((b) =>
    b.addEventListener('click', (e) => { e.preventDefault(); begin(); }));
  root.querySelectorAll('.xp-bar [data-act="play"]').forEach((b) =>
    b.addEventListener('click', () => { started ? toggle() : begin(); }));
  root.querySelectorAll('[data-frame]').forEach((b) =>
    b.addEventListener('click', () => { begin(); frame(b.dataset.frame); hideHint(); }));
  root.querySelectorAll('[data-zoom-by]').forEach((b) =>
    b.addEventListener('click', () => {
      begin(); zoomAt(s * parseFloat(b.dataset.zoomBy), stageW() / 2, stageH() / 2); hideHint();
    }));
  root.querySelectorAll('[data-act="whole"]').forEach((b) =>
    b.addEventListener('click', () => { begin(); whole(); hideHint(); }));
  root.querySelectorAll('[data-act="reset"]').forEach((b) =>
    b.addEventListener('click', () => { begin(); reset(); hideHint(); }));

  addEventListener('resize', () => layout(true));
  reset();
})();
