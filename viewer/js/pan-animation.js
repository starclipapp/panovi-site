const easeOutCubic = (progress) => 1 - ((1 - progress) ** 3);

const dimension = (value) => Number.isFinite(value) && value > 0 ? value : 0;
const point = (value) => ({
  x: Number.isFinite(value?.x) ? value.x : 0,
  y: Number.isFinite(value?.y) ? value.y : 0,
});

// Three presses cross the full movable range (from -bound to +bound).
export function panStepForBounds(bounds) {
  return {
    x: dimension(bounds?.x) * 2 / 3,
    y: dimension(bounds?.y) * 2 / 3,
  };
}

export function createTransformTransition({
  element,
  duration = 350,
  className = 'is-zoom-animating',
  setTimer = globalThis.setTimeout?.bind(globalThis),
  clearTimer = globalThis.clearTimeout?.bind(globalThis),
} = {}) {
  let timerId = null;

  function cancel() {
    if (timerId !== null) clearTimer?.(timerId);
    timerId = null;
    element?.classList.remove(className);
  }

  function begin() {
    if (timerId !== null) clearTimer?.(timerId);
    element?.classList.add(className);
    timerId = setTimer?.(() => {
      timerId = null;
      element?.classList.remove(className);
    }, duration) ?? null;
  }

  return { begin, cancel };
}

export function createPanAnimator({
  duration = 350,
  now = () => performance.now(),
  requestFrame = globalThis.requestAnimationFrame?.bind(globalThis),
  cancelFrame = globalThis.cancelAnimationFrame?.bind(globalThis),
  prefersReducedMotion = () => false,
} = {}) {
  let frameId = null;
  let target = null;

  function cancel() {
    if (frameId !== null) cancelFrame?.(frameId);
    frameId = null;
    target = null;
  }

  function animate({ from, to, onUpdate, onComplete = () => {} }) {
    cancel();
    const start = point(from);
    const destination = point(to);
    target = destination;

    if (
      prefersReducedMotion()
      || duration <= 0
      || (start.x === destination.x && start.y === destination.y)
    ) {
      onUpdate(destination);
      target = null;
      onComplete();
      return;
    }

    const startedAt = now();
    const step = (timestamp) => {
      const progress = Math.min(1, Math.max(0, (timestamp - startedAt) / duration));
      const eased = easeOutCubic(progress);
      onUpdate({
        x: start.x + ((destination.x - start.x) * eased),
        y: start.y + ((destination.y - start.y) * eased),
      });
      if (progress < 1) {
        frameId = requestFrame(step);
      } else {
        frameId = null;
        target = null;
        onComplete();
      }
    };

    frameId = requestFrame(step);
  }

  return {
    animate,
    cancel,
    getTarget: () => target && { ...target },
  };
}
