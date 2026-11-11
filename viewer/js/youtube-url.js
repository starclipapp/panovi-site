const VIDEO_ID_PATTERN = /^[A-Za-z0-9_-]{11}$/;

const YOUTUBE_HOSTS = new Set([
  "youtube.com",
  "www.youtube.com",
  "m.youtube.com",
  "music.youtube.com",
]);

const SHORT_HOSTS = new Set(["youtu.be", "www.youtu.be"]);

export function isYouTubeHost(hostname) {
  const host = String(hostname ?? '').toLowerCase();
  return YOUTUBE_HOSTS.has(host) || SHORT_HOSTS.has(host);
}

function validId(candidate) {
  return VIDEO_ID_PATTERN.test(candidate ?? "") ? candidate : null;
}

export function extractYouTubeVideoId(input) {
  const value = String(input ?? "").trim();
  if (!value) return null;
  if (VIDEO_ID_PATTERN.test(value)) return value;

  let url;
  try {
    url = new URL(value);
  } catch {
    return null;
  }

  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) {
    return null;
  }

  const host = url.hostname.toLowerCase();
  if (SHORT_HOSTS.has(host)) {
    return validId(url.pathname.split('/').filter(Boolean)[0]);
  }

  if (!YOUTUBE_HOSTS.has(host)) return null;

  if (url.pathname === '/watch') {
    return validId(url.searchParams.get('v'));
  }

  const segments = url.pathname.split('/').filter(Boolean);
  if (segments.length === 2 && ['shorts', 'embed'].includes(segments[0])) {
    return validId(segments[1]);
  }

  return null;
}
