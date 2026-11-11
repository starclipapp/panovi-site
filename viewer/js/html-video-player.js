import { t } from './i18n.js';

const MEDIA_ERROR_MESSAGES = {
  1: '動画の読み込みが中断されました。',
  2: 'ネットワークエラーで動画を読み込めませんでした。',
  3: '動画をデコードできませんでした。',
  4: 'この動画形式またはURLはブラウザで再生できません。',
};

export function describeMediaError(code) {
  return {
    code,
    kind: 'player-error',
    message: t(MEDIA_ERROR_MESSAGES[code] ?? '動画を読み込めませんでした。'),
  };
}

// Mirrors the YouTube adapter so app.js can drive either player the same way.
// State codes follow YouTube: 0 ended, 1 playing, 2 paused.
export function createHtmlVideoPlayer({
  mount,
  url,
  documentRef = globalThis.document,
  onReady = () => {},
  onStateChange = () => {},
  onMutedAutoplay = () => {},
  onError = () => {},
}) {
  const video = documentRef.createElement('video');
  video.className = 'html-video';
  video.controls = false;
  video.playsInline = true;
  video.preload = 'auto';
  video.setAttribute('playsinline', '');

  const adapter = {
    load(nextUrl) {
      video.src = nextUrl;
      video.load();
    },
    play() {
      const attempt = video.play();
      attempt?.catch?.((error) => {
        if (error?.name !== 'NotAllowedError' || video.muted) return;
        video.muted = true;
        video.play()?.then?.(onMutedAutoplay, () => {});
      });
    },
    pause() {
      video.pause();
    },
    toggle() {
      if (video.paused || video.ended) adapter.play();
      else video.pause();
    },
    seekBy(seconds) {
      const current = Number(video.currentTime);
      const next = Math.max(0, (Number.isFinite(current) ? current : 0) + seconds);
      const duration = Number(video.duration);
      video.currentTime = Number.isFinite(duration) ? Math.min(duration, next) : next;
    },
    seekToPercent(percent) {
      const duration = Number(video.duration);
      if (!Number.isFinite(duration) || duration <= 0) return;
      const clampedPercent = Math.min(100, Math.max(0, Number(percent) || 0));
      video.currentTime = duration * clampedPercent / 100;
    },
    toggleMute() {
      video.muted = !video.muted;
    },
    changeVolume(delta) {
      const current = Number(video.volume) * 100;
      const next = Math.min(100, Math.max(0, (Number.isFinite(current) ? current : 0) + delta));
      video.volume = next / 100;
      if (next > 0) video.muted = false;
    },
    getAspectRatio() {
      return video.videoWidth > 0 && video.videoHeight > 0
        ? video.videoWidth / video.videoHeight
        : null;
    },
    getState() {
      if (video.ended) return 0;
      return video.paused ? 2 : 1;
    },
    destroy() {
      video.pause();
      video.removeAttribute('src');
      video.load();
      video.remove();
    },
  };

  video.addEventListener('loadedmetadata', () => onReady(adapter));
  video.addEventListener('play', () => onStateChange(1));
  video.addEventListener('pause', () => onStateChange(2));
  video.addEventListener('ended', () => onStateChange(0));
  video.addEventListener('error', () => {
    if (!video.getAttribute('src')) return;
    onError(describeMediaError(video.error?.code));
  });

  mount.append(video);
  adapter.load(url);
  return adapter;
}
