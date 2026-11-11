import { extractYouTubeVideoId, isYouTubeHost } from './youtube-url.js';

export function parseVideoSource(input) {
  const value = String(input ?? '').trim();
  const videoId = extractYouTubeVideoId(value);
  if (videoId) {
    return {
      kind: 'youtube',
      videoId,
      key: videoId,
      url: `https://www.youtube.com/watch?v=${videoId}`,
    };
  }

  let url;
  try {
    url = new URL(value);
  } catch {
    return null;
  }

  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) {
    return null;
  }
  if (isYouTubeHost(url.hostname)) return null;

  url.hash = '';
  return { kind: 'file', key: `url:${url.href}`, url: url.href };
}

export function sourceInputFromSearch(search) {
  const params = new URLSearchParams(search);
  return params.get('url')?.trim() || null;
}

export function searchForSource(source) {
  return `?${new URLSearchParams({ url: source.url })}`;
}
