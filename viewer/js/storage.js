const SCHEMA_VERSION = 1;
import { ABSOLUTE_MAX_SCALE } from "./viewport-model.js";

const KEY_PREFIX = "panovi-viewer:viewport:v1:";

export function defaultViewportState() {
  return { scale: 1, x: 0, y: 0 };
}

function isValidState(value) {
  return value !== null
    && typeof value === "object"
    && Number.isFinite(value.scale)
    && value.scale >= 1
    && value.scale <= ABSOLUTE_MAX_SCALE
    && Number.isFinite(value.x)
    && Number.isFinite(value.y);
}

function storageKey(videoId) {
  return `${KEY_PREFIX}${videoId}`;
}

export function loadViewportState(videoId, storage = globalThis.localStorage) {
  const key = storageKey(videoId);
  let serialized;
  try {
    serialized = storage?.getItem(key);
  } catch {
    return defaultViewportState();
  }

  if (serialized === null || serialized === undefined) {
    return defaultViewportState();
  }

  try {
    const payload = JSON.parse(serialized);
    if (payload?.version !== SCHEMA_VERSION || !isValidState(payload)) {
      throw new TypeError("Invalid viewport payload");
    }
    return { scale: payload.scale, x: payload.x, y: payload.y };
  } catch {
    try {
      storage?.removeItem(key);
    } catch {
      // A blocked storage backend should not make the viewer unusable.
    }
    return defaultViewportState();
  }
}

export function saveViewportState(videoId, state, storage = globalThis.localStorage) {
  if (!isValidState(state)) {
    throw new TypeError("Expected a valid viewport state");
  }

  storage?.setItem(storageKey(videoId), JSON.stringify({
    version: SCHEMA_VERSION,
    scale: state.scale,
    x: state.x,
    y: state.y,
  }));
}

export function createViewportSaveScheduler({
  storage = globalThis.localStorage,
  delay = 180,
  setTimer = globalThis.setTimeout,
  clearTimer = globalThis.clearTimeout,
} = {}) {
  const timers = new Map();

  return {
    schedule(videoId, state, onError = () => {}) {
      if (!videoId) return;
      if (timers.has(videoId)) clearTimer(timers.get(videoId));
      const snapshot = { ...state };
      const timer = setTimer(() => {
        timers.delete(videoId);
        try {
          saveViewportState(videoId, snapshot, storage);
        } catch (error) {
          onError(error);
        }
      }, delay);
      timers.set(videoId, timer);
    },

    cancelAll() {
      for (const timer of timers.values()) clearTimer(timer);
      timers.clear();
    },
  };
}
