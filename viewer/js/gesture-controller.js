const DRAG_THRESHOLD = 4;
const DOUBLE_TAP_DELAY = 300;
const DOUBLE_TAP_DISTANCE = 28;
const WHEEL_SENSITIVITY = 0.0015;

const distance = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
const midpoint = (a, b) => ({ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 });

export function createGestureController({
  element,
  viewportModel,
  getSize,
  onChange,
  onActivate = () => {},
  setTimer = globalThis.setTimeout,
  clearTimer = globalThis.clearTimeout,
}) {
  let enabled = false;
  let dragging = false;
  let gestureSuppressed = false;
  let pinch = null;
  let lastTap = null;
  let tapTimer = null;
  const pointers = new Map();
  const hostWindow = element.ownerDocument?.defaultView;

  function localPoint(event) {
    const rect = element.getBoundingClientRect();
    return { x: event.clientX - rect.left, y: event.clientY - rect.top };
  }

  function releasePointer(pointerId) {
    if (element.hasPointerCapture?.(pointerId)) {
      element.releasePointerCapture(pointerId);
    }
  }

  function clearPointers() {
    for (const pointerId of pointers.keys()) releasePointer(pointerId);
    pointers.clear();
    pinch = null;
    dragging = false;
    gestureSuppressed = false;
    lastTap = null;
    if (tapTimer !== null) clearTimer(tapTimer);
    tapTimer = null;
    element.classList.remove('is-dragging');
  }

  function beginPinch() {
    const [first, second] = [...pointers.values()];
    if (!first || !second) {
      pinch = null;
      return;
    }
    pinch = {
      distance: Math.max(1, distance(first, second)),
      midpoint: midpoint(first, second),
      scale: viewportModel.getState().scale,
    };
    dragging = false;
    gestureSuppressed = true;
    element.classList.add('is-dragging');
  }

  function handleWheel(event) {
    if (!enabled) return;
    event.preventDefault();
    const nextScale = viewportModel.getState().scale * Math.exp(-event.deltaY * WHEEL_SENSITIVITY);
    viewportModel.setScaleAt(nextScale, localPoint(event), getSize());
    onChange();
  }

  function handlePointerDown(event) {
    if (!enabled) return;
    if (Number.isFinite(event.button) && event.button !== 0) return;
    const point = localPoint(event);
    pointers.set(event.pointerId, { ...point, startX: point.x, startY: point.y, pointerType: event.pointerType });
    element.setPointerCapture?.(event.pointerId);
    if (pointers.size === 2) beginPinch();
  }

  function handlePointerMove(event) {
    if (!enabled || !pointers.has(event.pointerId)) return;
    const point = localPoint(event);
    const previous = pointers.get(event.pointerId);
    pointers.set(event.pointerId, { ...previous, ...point });

    if (pointers.size >= 2) {
      const [first, second] = [...pointers.values()];
      const currentMidpoint = midpoint(first, second);
      const currentDistance = Math.max(1, distance(first, second));
      const baseline = pinch ?? {
        distance: currentDistance,
        midpoint: currentMidpoint,
        scale: viewportModel.getState().scale,
      };
      const size = getSize();
      viewportModel.setScaleAt(
        baseline.scale * (currentDistance / baseline.distance),
        baseline.midpoint,
        size,
      );
      viewportModel.panBy({
        x: currentMidpoint.x - baseline.midpoint.x,
        y: currentMidpoint.y - baseline.midpoint.y,
      }, size);
      pinch = {
        distance: currentDistance,
        midpoint: currentMidpoint,
        scale: viewportModel.getState().scale,
      };
      onChange();
      return;
    }

    if (!dragging) {
      const traveled = Math.hypot(point.x - previous.startX, point.y - previous.startY);
      if (traveled < DRAG_THRESHOLD) return;
      dragging = true;
      gestureSuppressed = true;
      element.classList.add('is-dragging');
      viewportModel.panBy({ x: point.x - previous.startX, y: point.y - previous.startY }, getSize());
    } else {
      viewportModel.panBy({ x: point.x - previous.x, y: point.y - previous.y }, getSize());
    }
    onChange();
  }

  function handleTouchTap(event, pointer) {
    const now = Number.isFinite(event.timeStamp) ? event.timeStamp : Date.now();
    if (lastTap && now - lastTap.time <= DOUBLE_TAP_DELAY && distance(lastTap, pointer) <= DOUBLE_TAP_DISTANCE) {
      if (tapTimer !== null) clearTimer(tapTimer);
      tapTimer = null;
      viewportModel.reset();
      onChange();
      lastTap = null;
      return;
    }
    lastTap = { ...pointer, time: now };
    tapTimer = setTimer(() => {
      tapTimer = null;
      lastTap = null;
      onActivate();
    }, DOUBLE_TAP_DELAY);
  }

  function handlePointerEnd(event) {
    if (!pointers.has(event.pointerId)) return;
    if (event.type === 'pointercancel') {
      clearPointers();
      return;
    }
    const pointer = pointers.get(event.pointerId);
    const isFinalPointer = pointers.size === 1;
    if (event.type === 'pointerup' && isFinalPointer && !gestureSuppressed) {
      if (event.pointerType === 'touch') handleTouchTap(event, pointer);
      else onActivate();
    }
    releasePointer(event.pointerId);
    pointers.delete(event.pointerId);
    pinch = null;

    if (pointers.size === 1) {
      const remaining = [...pointers.values()][0];
      remaining.startX = remaining.x;
      remaining.startY = remaining.y;
    }
    dragging = false;
    if (pointers.size === 0) gestureSuppressed = false;
    element.classList.remove('is-dragging');
  }

  function handleDoubleClick(event) {
    if (!enabled) return;
    event.preventDefault?.();
    viewportModel.reset();
    onChange();
  }

  element.addEventListener('pointerdown', handlePointerDown);
  element.addEventListener('pointermove', handlePointerMove);
  element.addEventListener('pointerup', handlePointerEnd);
  element.addEventListener('pointercancel', handlePointerEnd);
  element.addEventListener('dblclick', handleDoubleClick);
  hostWindow?.addEventListener('blur', clearPointers);

  return {
    setEnabled(nextEnabled) {
      const shouldEnable = Boolean(nextEnabled);
      if (shouldEnable === enabled) return;
      enabled = shouldEnable;
      if (enabled) {
        element.addEventListener('wheel', handleWheel, { passive: false });
      } else {
        element.removeEventListener('wheel', handleWheel);
        clearPointers();
      }
    },

    destroy() {
      if (enabled) element.removeEventListener('wheel', handleWheel);
      clearPointers();
      element.removeEventListener('pointerdown', handlePointerDown);
      element.removeEventListener('pointermove', handlePointerMove);
      element.removeEventListener('pointerup', handlePointerEnd);
      element.removeEventListener('pointercancel', handlePointerEnd);
      element.removeEventListener('dblclick', handleDoubleClick);
      hostWindow?.removeEventListener('blur', clearPointers);
      enabled = false;
    },
  };
}
