import { t } from './i18n.js';
import { createGestureController } from './gesture-controller.js';
import {
  beginQualityPlayback,
  createQualityGateModel,
  interactionModeForFullscreen,
  labelForYouTubeQuality,
} from './quality-gate.js';
import { createLatestRequestGate } from './request-gate.js';
import { createPanAnimator, createTransformTransition, panStepForBounds } from './pan-animation.js';
import { classifyShortcut, isShortcutTypingTarget } from './shortcuts.js';
import { createViewportSaveScheduler, loadViewportState } from './storage.js';
import { createViewportModel } from './viewport-model.js';
import { createHtmlVideoPlayer } from './html-video-player.js';
import { parseVideoSource, searchForSource, sourceInputFromSearch } from './video-source.js';
import { createYouTubePlayer, loadYouTubeApi } from './youtube-player.js';

const elements = {
  form: document.querySelector('#url-form'),
  urlInput: document.querySelector('#youtube-url'),
  urlError: document.querySelector('#url-error'),
  viewerShell: document.querySelector('#viewer-shell'),
  viewport: document.querySelector('#viewer-viewport'),
  gestureLayer: document.querySelector('#gesture-layer'),
  transform: document.querySelector('#player-transform'),
  empty: document.querySelector('#empty-state'),
  loading: document.querySelector('#loading-state'),
  error: document.querySelector('#error-state'),
  errorTitle: document.querySelector('#player-error-title'),
  errorMessage: document.querySelector('#player-error-message'),
  retry: document.querySelector('#retry-button'),
  youtubeLink: document.querySelector('#open-youtube-link'),
  play: document.querySelector('#play-button'),
  playIcon: document.querySelector('#play-icon'),
  rewind: document.querySelector('#rewind-button'),
  forward: document.querySelector('#forward-button'),
  reset: document.querySelector('#reset-button'),
  openFullscreen: document.querySelector('#open-fullscreen'),
  exitFullscreen: document.querySelector('#exit-fullscreen-button'),
  zoomSlider: document.querySelector('#zoom-slider'),
  zoomReadout: document.querySelector('#zoom-readout'),
  qualityGate: document.querySelector('#quality-gate'),
  qualityStatus: document.querySelector('#quality-status'),
  qualityConfirm: document.querySelector('#quality-confirm-button'),
  qualitySettings: document.querySelector('#quality-settings-button'),
  helpButton: document.querySelector('#help-button'),
  helpDialog: document.querySelector('#shortcut-help'),
  helpClose: document.querySelector('#help-close-button'),
  scaleButtons: [...document.querySelectorAll('[data-scale]')],
  frameButtons: [...document.querySelectorAll('[data-frame]')],
  toast: document.querySelector('#toast'),
};

let currentSource = null;
let player = null;
let playerKind = null;
let viewportModel = createViewportModel();
/// 前に見た位置が無い状態か（初めて開いた動画）。
let viewportIsDefault = true;
let renderFrame = null;
let gestureController = null;
let lastViewportSize = null;
const requestGate = createLatestRequestGate();
const viewportSaver = createViewportSaveScheduler();
const qualityGate = createQualityGateModel();
const panAnimator = createPanAnimator({
  prefersReducedMotion: () => window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches ?? false,
});
const zoomTransition = createTransformTransition({ element: elements.transform });

function viewportSize() {
  const rect = elements.viewport.getBoundingClientRect();
  return { width: rect.width, height: rect.height };
}

function showOnlyState(target) {
  for (const state of [elements.empty, elements.loading, elements.error]) {
    state.classList.toggle('is-hidden', state !== target);
  }
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.remove('is-hidden');
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => elements.toast.classList.add('is-hidden'), 3200);
}

function scheduleSave(state) {
  if (!currentSource) return;
  viewportSaver.schedule(currentSource.key, state, () => {
    showToast(t('表示位置を保存できませんでした。'));
  });
}

function renderViewport({ persist = true, keepPanAnimation = false, animateZoom = false } = {}) {
  if (!keepPanAnimation) panAnimator.cancel();
  if (animateZoom) zoomTransition.begin();
  else zoomTransition.cancel();
  if (renderFrame !== null) cancelAnimationFrame(renderFrame);
  renderFrame = requestAnimationFrame(() => {
    const state = viewportModel.getState();
    elements.transform.style.transform = `translate3d(${state.x}px, ${state.y}px, 0) scale(${state.scale})`;
    elements.zoomReadout.textContent = `${Math.round(state.scale * 100)}%`;
    elements.zoomSlider.max = String(Math.round(viewportModel.getMaxScale(viewportSize()) * 100));
    elements.zoomSlider.value = String(Math.round(state.scale * 100));
    if (persist) scheduleSave(state);
    renderFrame = null;
  });
}

function animateViewportPan(target, size = viewportSize()) {
  const current = viewportModel.getState();
  panAnimator.animate({
    from: { x: current.x, y: current.y },
    to: { x: target.x, y: target.y },
    onUpdate: (position) => {
      const state = viewportModel.getState();
      viewportModel.panBy({ x: position.x - state.x, y: position.y - state.y }, size);
      renderViewport({ persist: false, keepPanAnimation: true });
    },
    onComplete: () => renderViewport({ keepPanAnimation: true }),
  });
}

function animateHorizontalPreset(preset) {
  const size = viewportSize();
  animateViewportPan(viewportModel.getHorizontalPreset(preset, size), size);
}

function animatePanBy(delta) {
  const size = viewportSize();
  const origin = panAnimator.getTarget() ?? viewportModel.getState();
  animateViewportPan(viewportModel.getPanTarget(delta, size, origin), size);
}

function setPlayerError(error) {
  qualityGate.cancel();
  renderQualityGate();
  elements.errorTitle.textContent = error.kind === 'embedding-disabled'
    ? t('この動画はここでは再生できません')
    : t('動画を読み込めませんでした');
  elements.errorMessage.textContent = error.message;
  showOnlyState(elements.error);
}

function updateSourceLink(source) {
  elements.youtubeLink.href = source.url;
  elements.youtubeLink.textContent = source.kind === 'youtube' ? t('YouTubeで開く ↗') : t('動画を直接開く ↗');
}

function setInteractionMode(mode) {
  if (mode === 'viewing' && qualityGate.getState().active) return false;

  elements.viewport.dataset.interactionMode = mode;
  gestureController?.setEnabled(mode === 'viewing');
  return true;
}

function renderQualityGate() {
  const state = qualityGate.getState();
  elements.qualityGate.classList.toggle('is-hidden', !state.active);
  elements.qualitySettings.classList.toggle('is-hidden', state.active || !state.videoId);
  elements.qualityStatus.textContent = state.reportedQuality
    ? `${t('YouTubeの現在の報告')}: ${labelForYouTubeQuality(state.reportedQuality)}`
    : t('映像をクリック／タップして操作バーを表示');
}

function beginQualityCheck(videoId) {
  beginQualityPlayback(qualityGate, player, videoId);
  setInteractionMode('youtube');
  renderQualityGate();
  showOnlyState(null);
}

function restoreViewport(sourceKey) {
  const saved = loadViewportState(sourceKey);
  // ★前に見た位置が無いときは、**黒帯の出ない大きさ**から始める（下の applyDefaultFraming）。
  //   横長の映像を scale 1（＝全体がレターボックス）で出すと、
  //   初見の人の画面は上下が黒い帯で埋まる。
  viewportIsDefault = saved.scale === 1 && saved.x === 0 && saved.y === 0;
  viewportModel = createViewportModel(saved);
  const size = viewportSize();
  viewportModel.resize(size, size);
  lastViewportSize = size;
  installGestureController();
  renderViewport({ persist: false });
}

function installGestureController() {
  gestureController?.destroy();
  gestureController = createGestureController({
    element: elements.gestureLayer,
    viewportModel,
    getSize: viewportSize,
    onChange: renderViewport,
    onActivate: () => player?.toggle(),
  });
  gestureController.setEnabled(elements.viewport.dataset.interactionMode === 'viewing');
}

function updatePlaybackState(state) {
  const playing = state === 1;
  elements.playIcon.textContent = playing ? 'Ⅱ' : '▶';
  elements.play.setAttribute('aria-label', playing ? t('一時停止') : t('再生'));
}

function mountPlayer(kind) {
  player?.destroy();
  player = null;
  playerKind = kind;
  updatePlaybackState(2);
  const mount = document.createElement('div');
  mount.id = 'player-mount';
  elements.transform.replaceChildren(mount);
  return mount;
}

function openFileVideo(source) {
  qualityGate.cancel();
  renderQualityGate();
  setInteractionMode('viewing');

  if (player && playerKind === 'file') {
    player.load(source.url);
    return;
  }

  player = createHtmlVideoPlayer({
    mount: mountPlayer('file'),
    url: source.url,
    onReady: (adapter) => {
      viewportModel.setContentAspect(adapter.getAspectRatio(), viewportSize());
      applyDefaultFraming();
      renderViewport({ persist: false });
      showOnlyState(null);
      adapter.play();
    },
    onStateChange: updatePlaybackState,
    onMutedAutoplay: () => showToast(t('自動再生のためミュートで再生中です。Mで解除できます。')),
    onError: setPlayerError,
  });
}

async function openVideo(input, { enterFullscreen = false } = {}) {
  const source = parseVideoSource(input);
  if (!source) {
    elements.urlError.textContent = t('YouTubeのURLまたは動画ファイル（mp4など）のURLを入力してください。');
    elements.urlInput.setAttribute('aria-invalid', 'true');
    return;
  }

  elements.urlError.textContent = '';
  elements.urlInput.removeAttribute('aria-invalid');
  if (enterFullscreen && !isFullscreen()) {
    void toggleFullscreen();
  }
  const request = requestGate.begin();
  currentSource = source;
  updateSourceLink(source);
  window.history.replaceState(null, '', searchForSource(source));
  showOnlyState(elements.loading);
  restoreViewport(source.key);

  if (source.kind === 'file') {
    openFileVideo(source);
    return;
  }

  const { videoId } = source;
  try {
    if (player && playerKind === 'youtube') {
      player.load(videoId);
      beginQualityCheck(videoId);
      return;
    }

    const yt = await loadYouTubeApi(document);
    if (!requestGate.isCurrent(request)) return;
    player = createYouTubePlayer({
      mountId: mountPlayer('youtube'),
      videoId,
      yt,
      onReady: () => beginQualityCheck(currentSource.videoId),
      onStateChange: updatePlaybackState,
      onPlaybackQualityChange: (quality) => {
        if (qualityGate.getState().videoId !== currentSource?.videoId) return;
        qualityGate.report(quality);
        renderQualityGate();
      },
      onError: setPlayerError,
    });
  } catch (error) {
    if (!requestGate.isCurrent(request)) return;
    setPlayerError({
      kind: 'api-error',
      message: error instanceof Error ? error.message : t('YouTube APIを読み込めませんでした。'),
    });
  }
}

elements.form.addEventListener('submit', (event) => {
  event.preventDefault();
  openVideo(elements.urlInput.value, { enterFullscreen: elements.openFullscreen.checked });
});

elements.retry.addEventListener('click', () => openVideo(elements.urlInput.value));
elements.play.addEventListener('click', () => player?.toggle());
elements.rewind.addEventListener('click', () => player?.seekBy(-10));
elements.forward.addEventListener('click', () => player?.seekBy(10));
elements.qualityConfirm.addEventListener('click', () => {
  qualityGate.confirm();
  renderQualityGate();
  setInteractionMode('viewing');
});
elements.qualitySettings.addEventListener('click', () => {
  if (currentSource?.kind !== 'youtube') return;
  qualityGate.begin(currentSource.videoId);
  setInteractionMode('youtube');
  renderQualityGate();
});

function toggleHelp() {
  if (elements.helpDialog.open) elements.helpDialog.close();
  else elements.helpDialog.showModal();
}

elements.helpButton.addEventListener('click', toggleHelp);
elements.helpClose.addEventListener('click', () => elements.helpDialog.close());
elements.helpDialog.addEventListener('click', (event) => {
  if (event.target === elements.helpDialog) elements.helpDialog.close();
});

/// 初めて開いた動画の始めの見え方。
/// ★**黒帯を出さない**ところまで寄せる（`getFillScale`＝映像が画面を覆う倍率）。
///   横長のパノラマでは、ここが「16:9 に切り出した状態」にあたる。
///   前に見た位置があるときは触らない（その人の続きを壊さない）。
function applyDefaultFraming() {
  if (!viewportIsDefault) return;
  const size = viewportSize();
  const fill = viewportModel.getFillScale(size);
  if (!Number.isFinite(fill) || fill <= 1) return;
  viewportModel.setScaleAt(fill, { x: size.width / 2, y: size.height / 2 }, size);
}

function presetScale(preset, size) {
  const fill = viewportModel.getFillScale(size);
  if (preset === 'fill') return fill;
  if (preset === 'fill-2') return fill * 2;
  return Number(preset);
}

elements.scaleButtons.forEach((button) => {
  button.addEventListener('click', () => {
    const size = viewportSize();
    viewportModel.setScaleAt(presetScale(button.dataset.scale, size), {
      x: size.width / 2,
      y: size.height / 2,
    }, size);
    renderViewport({ animateZoom: true });
  });
});

elements.zoomSlider.addEventListener('input', () => {
  const size = viewportSize();
  viewportModel.setScaleAt(Number(elements.zoomSlider.value) / 100, {
    x: size.width / 2,
    y: size.height / 2,
  }, size);
  renderViewport();
});

elements.frameButtons.forEach((button) => {
  button.addEventListener('click', () => animateHorizontalPreset(button.dataset.frame));
});

elements.reset.addEventListener('click', () => {
  // ★scale 1 に戻すと**また上下に黒帯**が出る。覆う大きさへ戻す。
  viewportModel.reset();
  const size = viewportSize();
  const fill = viewportModel.getFillScale(size);
  if (Number.isFinite(fill) && fill > 1) {
    viewportModel.setScaleAt(fill, { x: size.width / 2, y: size.height / 2 }, size);
  }
  renderViewport();
});

// iPhone Safari has no element Fullscreen API, so the viewer instead covers
// the page with a fixed layer ("pseudo fullscreen") that reuses the same styles.
const supportsNativeFullscreen = Boolean(
  document.fullscreenEnabled && elements.viewerShell.requestFullscreen,
);

function isPseudoFullscreen() {
  return elements.viewerShell.classList.contains('is-pseudo-fullscreen');
}

function isFullscreen() {
  return document.fullscreenElement === elements.viewerShell || isPseudoFullscreen();
}

function setPseudoFullscreen(active) {
  lastViewportSize = viewportSize();
  if (active) setInteractionMode(interactionModeForFullscreen(qualityGate.getState().active));
  elements.viewerShell.classList.toggle('is-pseudo-fullscreen', active);
  document.documentElement.classList.toggle('has-pseudo-fullscreen', active);
  syncViewportSize();
}

async function toggleFullscreen() {
  if (!supportsNativeFullscreen) {
    setPseudoFullscreen(!isPseudoFullscreen());
    return;
  }

  try {
    if (document.fullscreenElement === elements.viewerShell) {
      await document.exitFullscreen();
    } else {
      lastViewportSize = viewportSize();
      setInteractionMode(interactionModeForFullscreen(qualityGate.getState().active));
      await elements.viewerShell.requestFullscreen();
    }
  } catch {
    showToast(t('フルスクリーン表示を開始できませんでした。'));
  }
}

function syncViewportSize() {
  requestAnimationFrame(() => {
    const nextSize = viewportSize();
    viewportModel.resize(lastViewportSize ?? nextSize, nextSize);
    lastViewportSize = nextSize;
    renderViewport();
  });
}

document.addEventListener('fullscreenchange', syncViewportSize);
window.addEventListener('resize', syncViewportSize);
elements.exitFullscreen.addEventListener('click', () => setPseudoFullscreen(false));

function zoomBy(factor) {
  const size = viewportSize();
  viewportModel.setScaleAt(viewportModel.getState().scale * factor, {
    x: size.width / 2,
    y: size.height / 2,
  }, size);
  renderViewport({ animateZoom: true });
}

function executeCommand(command) {
  if (command.startsWith('seek-percent-')) {
    player?.seekToPercent(Number(command.slice('seek-percent-'.length)));
    return;
  }

  const size = viewportSize();
  const panStep = panStepForBounds(viewportModel.getPanBounds(size));
  const actions = {
    'toggle-play': () => player?.toggle(),
    'seek-backward-5': () => player?.seekBy(-5),
    'seek-forward-5': () => player?.seekBy(5),
    'seek-backward-10': () => player?.seekBy(-10),
    'seek-forward-10': () => player?.seekBy(10),
    'toggle-mute': () => player?.toggleMute(),
    'volume-up': () => player?.changeVolume(5),
    'volume-down': () => player?.changeVolume(-5),
    'zoom-in': () => zoomBy(1.2),
    'zoom-out': () => zoomBy(1 / 1.2),
    'pan-left': () => animatePanBy({ x: -panStep.x, y: 0 }),
    'pan-right': () => animatePanBy({ x: panStep.x, y: 0 }),
    'pan-up': () => animatePanBy({ x: 0, y: -panStep.y }),
    'pan-down': () => animatePanBy({ x: 0, y: panStep.y }),
    reset: () => { viewportModel.reset(); renderViewport(); },
    fullscreen: toggleFullscreen,
    'toggle-help': toggleHelp,
  };
  actions[command]?.();
}

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && isPseudoFullscreen() && !elements.helpDialog.open) {
    event.preventDefault();
    setPseudoFullscreen(false);
    return;
  }
  const command = classifyShortcut(
    event,
    isShortcutTypingTarget(event.target),
    elements.helpDialog.open,
  );
  if (!command) return;
  event.preventDefault();
  executeCommand(command);
});

lastViewportSize = viewportSize();
installGestureController();
renderViewport({ persist: false });
renderQualityGate();

const initialInput = sourceInputFromSearch(window.location.search);
if (initialInput) {
  elements.urlInput.value = initialInput;
  openVideo(initialInput);
}
