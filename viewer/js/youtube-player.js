import { t } from './i18n.js';

const apiLoads = new WeakMap();

export function loadYouTubeApi(documentRef = globalThis.document) {
  const windowRef = documentRef?.defaultView ?? globalThis.window;
  if (windowRef?.YT?.Player) return Promise.resolve(windowRef.YT);
  if (apiLoads.has(documentRef)) return apiLoads.get(documentRef);

  const promise = new Promise((resolve, reject) => {
    const script = documentRef.createElement('script');
    const previousReady = windowRef.onYouTubeIframeAPIReady;
    script.src = 'https://www.youtube.com/iframe_api';
    script.async = true;
    script.dataset.panoviViewerYoutubeApi = 'true';

    windowRef.onYouTubeIframeAPIReady = () => {
      previousReady?.();
      if (windowRef.YT?.Player) {
        resolve(windowRef.YT);
      } else {
        apiLoads.delete(documentRef);
        reject(new Error('YouTube API did not expose a player.'));
      }
    };

    script.onerror = () => {
      apiLoads.delete(documentRef);
      windowRef.onYouTubeIframeAPIReady = previousReady;
      reject(new Error(t('YouTube APIの読み込みに失敗しました。')));
    };

    documentRef.head.append(script);
  });

  apiLoads.set(documentRef, promise);
  return promise;
}

export function describeYouTubeError(code) {
  if (code === 101 || code === 150) {
    return {
      code,
      kind: 'embedding-disabled',
      message: t('この動画は埋め込み再生が許可されていません。YouTubeで開いてください。'),
    };
  }

  const messages = {
    2: 'YouTube動画IDが正しくありません。',
    5: 'このブラウザでは動画を再生できません。',
    100: '動画が見つからないか、非公開になっています。',
  };
  return {
    code,
    kind: 'player-error',
    message: t(messages[code] ?? 'YouTube動画を読み込めませんでした。'),
  };
}

export function createYouTubePlayer({
  mountId,
  videoId,
  onReady = () => {},
  onStateChange = () => {},
  onPlaybackQualityChange = () => {},
  onError = () => {},
  yt,
}) {
  let rawPlayer;

  const adapter = {
    load(nextVideoId) {
      rawPlayer.loadVideoById(nextVideoId);
    },
    play() {
      rawPlayer.playVideo();
    },
    pause() {
      rawPlayer.pauseVideo();
    },
    toggle() {
      if (rawPlayer.getPlayerState() === 1) {
        rawPlayer.pauseVideo();
      } else {
        rawPlayer.playVideo();
      }
    },
    seekBy(seconds) {
      const current = Number(rawPlayer.getCurrentTime());
      rawPlayer.seekTo(Math.max(0, (Number.isFinite(current) ? current : 0) + seconds), true);
    },
    seekToPercent(percent) {
      const duration = Number(rawPlayer.getDuration());
      if (!Number.isFinite(duration) || duration <= 0) return;
      const clampedPercent = Math.min(100, Math.max(0, Number(percent) || 0));
      rawPlayer.seekTo(duration * clampedPercent / 100, true);
    },
    toggleMute() {
      if (rawPlayer.isMuted()) rawPlayer.unMute();
      else rawPlayer.mute();
    },
    changeVolume(delta) {
      const current = Number(rawPlayer.getVolume());
      const next = Math.min(100, Math.max(0, (Number.isFinite(current) ? current : 0) + delta));
      rawPlayer.setVolume(next);
    },
    getState() {
      return rawPlayer.getPlayerState();
    },
    destroy() {
      rawPlayer.destroy();
    },
  };

  rawPlayer = new yt.Player(mountId, {
    videoId,
    playerVars: {
      autoplay: 1,
      controls: 1,
      disablekb: 0,
      enablejsapi: 1,
      playsinline: 1,
    },
    events: {
      onReady: () => onReady(adapter),
      onStateChange: (event) => onStateChange(event.data),
      onPlaybackQualityChange: (event) => onPlaybackQualityChange(event.data),
      onError: (event) => onError(describeYouTubeError(event.data)),
    },
  });

  return adapter;
}
