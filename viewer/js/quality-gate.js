import { t } from './i18n.js';

const QUALITY_LABELS = {
  small: '240p以下',
  medium: '360p',
  large: '480p',
  hd720: '720p',
  hd1080: '1080p',
  highres: '1080p超',
};

export function labelForYouTubeQuality(quality) {
  return t(QUALITY_LABELS[quality] ?? '自動調整');
}

export function interactionModeForFullscreen(qualityCheckActive) {
  return qualityCheckActive ? 'youtube' : 'viewing';
}

export function beginQualityPlayback(qualityGate, player, videoId) {
  qualityGate.begin(videoId);
  player?.play();
}

export function createQualityGateModel() {
  let state = {
    active: false,
    videoId: null,
    reportedQuality: null,
  };

  const snapshot = () => ({ ...state });

  return {
    begin(videoId) {
      state = {
        active: true,
        videoId,
        reportedQuality: null,
      };
      return snapshot();
    },
    report(quality) {
      if (state.active) {
        state = { ...state, reportedQuality: quality };
      }
      return snapshot();
    },
    confirm() {
      state = { ...state, active: false };
      return snapshot();
    },
    cancel() {
      state = {
        active: false,
        videoId: null,
        reportedQuality: null,
      };
      return snapshot();
    },
    getState: snapshot,
  };
}
