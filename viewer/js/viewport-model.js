const MIN_SCALE = 1;
const BASE_MAX_SCALE = 5;
// Zoom headroom beyond the scale where the media first covers the viewport.
const FILL_ZOOM_HEADROOM = 3;
export const ABSOLUTE_MAX_SCALE = 40;

function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, value));
}

function scaleValue(value, fallback, maximum = ABSOLUTE_MAX_SCALE) {
  if (value === Infinity) return maximum;
  if (value === -Infinity) return MIN_SCALE;
  if (!Number.isFinite(value)) return fallback;
  return clamp(value, MIN_SCALE, maximum);
}

function validDimension(value) {
  return Number.isFinite(value) && value > 0 ? value : 0;
}

function validAspect(value) {
  return Number.isFinite(value) && value > 0 ? value : null;
}

// Size of the media letterboxed ("contain") inside the viewport at scale 1.
// Without a known aspect the media is assumed to fill the viewport.
function contentSize(size, aspect) {
  const width = validDimension(size?.width);
  const height = validDimension(size?.height);
  if (!aspect || !width || !height) return { width, height };
  return width / height < aspect
    ? { width, height: width / aspect }
    : { width: height * aspect, height };
}

export function fillScaleFor(size, aspect) {
  const content = contentSize(size, validAspect(aspect));
  if (!content.width || !content.height) return MIN_SCALE;
  return Math.max(size.width / content.width, size.height / content.height);
}

export function maxScaleFor(size, aspect) {
  return Math.min(
    ABSOLUTE_MAX_SCALE,
    Math.max(BASE_MAX_SCALE, fillScaleFor(size, aspect) * FILL_ZOOM_HEADROOM),
  );
}

function boundsFor(scale, size, aspect) {
  const width = validDimension(size?.width);
  const height = validDimension(size?.height);
  const content = contentSize(size, aspect);
  return {
    x: Math.max(0, (scale * content.width - width) / 2),
    y: Math.max(0, (scale * content.height - height) / 2),
  };
}

function clampState(state, size, aspect) {
  const bounds = boundsFor(state.scale, size, aspect);
  return {
    scale: state.scale,
    x: clamp(Number.isFinite(state.x) ? state.x : 0, -bounds.x, bounds.x),
    y: clamp(Number.isFinite(state.y) ? state.y : 0, -bounds.y, bounds.y),
  };
}

function horizontalPresetState(state, preset, size, aspect) {
  if (!['left', 'center', 'right'].includes(preset)) {
    throw new RangeError(`Unknown horizontal preset: ${preset}`);
  }
  const bounds = boundsFor(state.scale, size, aspect);
  const x = preset === 'left' ? bounds.x : preset === 'right' ? -bounds.x : 0;
  return clampState({ ...state, x }, size, aspect);
}

export function createViewportModel(initialState = {}) {
  let state = {
    scale: scaleValue(initialState.scale ?? 1, 1),
    x: Number.isFinite(initialState.x) ? initialState.x : 0,
    y: Number.isFinite(initialState.y) ? initialState.y : 0,
  };
  let aspect = null;

  const snapshot = () => ({ ...state });

  return {
    getState: snapshot,

    setContentAspect(nextAspect, size) {
      aspect = validAspect(nextAspect);
      state = clampState({
        ...state,
        scale: scaleValue(state.scale, 1, maxScaleFor(size, aspect)),
      }, size, aspect);
      return snapshot();
    },

    getFillScale(size) {
      return fillScaleFor(size, aspect);
    },

    getMaxScale(size) {
      return maxScaleFor(size, aspect);
    },

    getPanBounds(size) {
      return boundsFor(state.scale, size, aspect);
    },

    reset() {
      state = { scale: 1, x: 0, y: 0 };
      return snapshot();
    },

    setScaleAt(nextScale, focal, size) {
      const scale = scaleValue(nextScale, state.scale, maxScaleFor(size, aspect));
      const width = validDimension(size?.width);
      const height = validDimension(size?.height);
      const focalX = Number.isFinite(focal?.x) ? focal.x : width / 2;
      const focalY = Number.isFinite(focal?.y) ? focal.y : height / 2;
      const relativeX = focalX - width / 2;
      const relativeY = focalY - height / 2;
      const mediaX = (relativeX - state.x) / state.scale;
      const mediaY = (relativeY - state.y) / state.scale;

      state = clampState({
        scale,
        x: relativeX - mediaX * scale,
        y: relativeY - mediaY * scale,
      }, size, aspect);
      return snapshot();
    },

    panBy(delta, size) {
      state = clampState({
        scale: state.scale,
        x: state.x + (Number.isFinite(delta?.x) ? delta.x : 0),
        y: state.y + (Number.isFinite(delta?.y) ? delta.y : 0),
      }, size, aspect);
      return snapshot();
    },

    getHorizontalPreset(preset, size) {
      return horizontalPresetState(state, preset, size, aspect);
    },

    getPanTarget(delta, size, origin = state) {
      const originX = Number.isFinite(origin?.x) ? origin.x : state.x;
      const originY = Number.isFinite(origin?.y) ? origin.y : state.y;
      return clampState({
        scale: state.scale,
        x: originX + (Number.isFinite(delta?.x) ? delta.x : 0),
        y: originY + (Number.isFinite(delta?.y) ? delta.y : 0),
      }, size, aspect);
    },

    setHorizontalPreset(preset, size) {
      state = horizontalPresetState(state, preset, size, aspect);
      return snapshot();
    },

    resize(previousSize, nextSize) {
      const previousContent = contentSize(previousSize, aspect);
      const nextContent = contentSize(nextSize, aspect);
      // A view that covered the viewport keeps covering it at the same relative
      // zoom (rotation, mobile toolbars); a letterboxed view keeps its scale.
      const previousFill = fillScaleFor(previousSize, aspect);
      const scale = state.scale >= previousFill
        ? scaleValue(
          state.scale * fillScaleFor(nextSize, aspect) / previousFill,
          state.scale,
          maxScaleFor(nextSize, aspect),
        )
        : scaleValue(state.scale, state.scale, maxScaleFor(nextSize, aspect));
      // Keep the same point of the media at the viewport center.
      const offset = (value, previous, next) => (previous > 0
        ? value / (state.scale * previous) * scale * next
        : value);

      state = clampState({
        scale,
        x: offset(state.x, previousContent.width, nextContent.width),
        y: offset(state.y, previousContent.height, nextContent.height),
      }, nextSize, aspect);
      return snapshot();
    },
  };
}
