import 'hls-video-element';
import Hls from 'hls.js';

const HLS_SRC = 'https://devstreaming-cdn.apple.com/videos/streaming/examples/adv_dv_atmos/main.m3u8';

window.addEventListener('DOMContentLoaded', () => {
  const hlsVideoEl = document.getElementById('hls-video-el');
  hlsVideoEl.config = {};
  hlsVideoEl.src = HLS_SRC;
  window.__hlsVideoEl = hlsVideoEl;
  queueMicrotask(() => {
    window.__hlsApi = hlsVideoEl.api;
    hlsVideoEl.api?.on(Hls.Events.MANIFEST_PARSED, () => {
      window.__manifestParsed = true;
    });
  });

  const plainVideoEl = document.getElementById('plain-video-el');
  window.__plainVideoEl = plainVideoEl;
});
