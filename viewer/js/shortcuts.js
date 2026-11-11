const COMMANDS = new Map([
  [' ', 'toggle-play'],
  ['k', 'toggle-play'],
  ['j', 'seek-backward-10'],
  ['l', 'seek-forward-10'],
  ['m', 'toggle-mute'],
  ['+', 'zoom-in'],
  ['=', 'zoom-in'],
  ['-', 'zoom-out'],
  ['?', 'toggle-help'],
]);

const NON_TYPING_INPUT_TYPES = new Set([
  'button',
  'checkbox',
  'color',
  'file',
  'hidden',
  'image',
  'radio',
  'range',
  'reset',
  'submit',
]);

export function isShortcutTypingTarget(target) {
  if (!target || typeof target !== 'object') return false;
  if (target.isContentEditable) return true;

  const tagName = target.tagName?.toUpperCase();
  if (tagName === 'TEXTAREA') return true;
  if (tagName !== 'INPUT') return false;
  return !NON_TYPING_INPUT_TYPES.has(String(target.type || 'text').toLowerCase());
}

export function classifyShortcut(event, editableTarget = false, helpOpen = false) {
  if (editableTarget || event.metaKey || event.ctrlKey || event.altKey) return null;

  const normalized = event.key?.length === 1 ? event.key.toLowerCase() : event.key;
  if (helpOpen) return normalized === '?' ? 'toggle-help' : null;

  if (event.key === 'ArrowLeft') return event.shiftKey ? 'seek-backward-10' : 'pan-right';
  if (event.key === 'ArrowRight') return event.shiftKey ? 'seek-forward-10' : 'pan-left';
  if (event.key === 'ArrowUp') return event.shiftKey ? null : 'zoom-in';
  if (event.key === 'ArrowDown') return event.shiftKey ? null : 'zoom-out';
  if (event.key === 'Home') return 'seek-percent-0';

  if (/^[0-9]$/.test(normalized)) return `seek-percent-${Number(normalized) * 10}`;
  if (normalized === 'r') return 'reset';
  if (normalized === 'f') return 'fullscreen';
  return COMMANDS.get(normalized) ?? null;
}
