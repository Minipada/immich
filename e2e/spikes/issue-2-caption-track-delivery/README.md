# Spike: caption track delivery and language detection library (#2)

Verification artifacts for the four load-bearing assumptions in #2. Findings are
recorded in full on the issue; this directory holds the reproducible test harness.

## Checks 1 & 2 — `hls-video` track forwarding and HLS subtitle independence

`index.html` + `entry.js` load the exact `hls-video-element` / `hls.js` packages
pinned in `web/package.json`, with a hardcoded `<track>` child pointing at
`spike-test.vtt`.

Reproduce:

```sh
# from repo root, with web/ dependencies installed
node node_modules/.pnpm/esbuild@*/node_modules/esbuild/bin/esbuild \
  e2e/spikes/issue-2-caption-track-delivery/entry.js \
  --bundle --format=esm --platform=browser \
  --outfile=e2e/spikes/issue-2-caption-track-delivery/bundle.js

cd e2e/spikes/issue-2-caption-track-delivery && python3 -m http.server 8955
# open http://127.0.0.1:8955/index.html
```

`entry.js` sets `src` on `<hls-video>` to a public HLS stream. Swap between:

- `https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8` — no manifest subtitle group
  (matches Immich's own HLS output today).
- `https://devstreaming-cdn.apple.com/videos/streaming/examples/adv_dv_atmos/main.m3u8`
  — has a real `SUBTITLES` media group, to exercise hls.js's subtitle track
  controller directly.

**Result:** the light-DOM `<track>` is cloned by `custom-media-element` (the base
class of `hls-video-element`) into the real internal `<video>`'s `textTracks` list.
With the Apple stream, hls.js added its own 14 native `TextTrack` objects (13
subtitle languages + 1 id3 metadata track) for the manifest's `SUBTITLES` group —
our track remained present, untouched, at all times, including across an
`el.load()` reload cycle (the same recovery path `VideoNativeViewer.svelte` uses on
a 404'd fragment). hls.js's subtitle track controller and externally-added tracks
are confirmed independent.

Caveat found along the way: the browser's automatic "default track" selection did
not reliably enable our `<track default>` on its own inside this custom element —
`track.mode` had to be set explicitly (`'showing'`) before cues rendered. Real
players normally do this anyway to wire up a CC toggle button, so it isn't a new
requirement, just worth calling out for whoever builds the delivery slice.

## Check 3 — session credentials on the track fetch

`credential-test-server.py` is a minimal same-origin server: `/login` sets a
session cookie, `/protected.vtt` 200s only if that cookie is present (401
otherwise), `/page` serves a `<track src="/protected.vtt">` with no `crossorigin`
attribute — mirroring how Immich's video/track elements are written today (grep
confirms no `crossOrigin`/`crossorigin` is set anywhere in `web/src`).

Reproduce:

```sh
python3 e2e/spikes/issue-2-caption-track-delivery/credential-test-server.py
# in a browser: visit http://127.0.0.1:8956/login, then http://127.0.0.1:8956/page
# inspect the network tab for the /protected.vtt request
```

**Result:** after visiting `/login`, the `<track>`'s automatic fetch of
`/protected.vtt` returned 200 (cookie included) with no application code
involved — plain same-origin browser credentialing. Without the cookie the same
request 401s. This was cross-checked against the actual web app's service worker
(`web/src/service-worker/index.ts`), which only intercepts
`/api/assets/:id/(original|thumbnail)` — a route shape a caption endpoint is
unlikely to reuse — so no service-worker interference is expected either.

The full Immich dev stack (docker compose) was not spun up for this check; the
mechanism under test (native same-origin `<track>` credentialing, absent a
`crossorigin` attribute) is standard browser behaviour independent of the backend,
and was verified directly against the code paths (video element markup, service
worker scope) that would carry a real caption URL.

## Check 4 — `faster-whisper` per-window language detection parameter

Pure library lookup, no harness needed. `WhisperModel.transcribe()` (and
`TranscriptionOptions`) exposes:

```python
multilingual: bool = False
```

docstring: "Perform language detection on every segment." Introduced in
`faster-whisper` **v1.1.0**; the parameter name and behavior are unchanged through
the current latest release, **v1.2.1** (2025-10-31). When set, `generate_segments()`
calls `self.model.detect_language(encoder_output)` per segment inside the main
decode loop rather than once for the whole request, and the library forces it back
to `False` (with a warning) if the loaded model is English-only — consistent with
the PRD's disqualification of the distilled (English-only) variants.
