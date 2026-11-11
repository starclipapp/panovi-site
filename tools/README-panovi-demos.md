# Panovi: mountain and city examples

The Japanese and English landing pages feature the mountain demo in the opening hero and show both examples below the stats. Each video contains the left and right camera recordings above the supplied stitched result, on the navy background used by the guide reference. These are **presentation montages**, not newly stitched exports.

- `img/demo-mountain.mp4` and `demo-mountain-poster.jpg`
- `img/demo-city.mp4` and `demo-city-poster.jpg`
- Both: 1280 × 840, 30 fps, 150 frames / 5 seconds, H.264 High Level 4.0, YUV420P, BT.709, no audio, MP4 fast start.
- Posters: frame at 2.5 seconds of each montage.

The existing `hero.mp4`, `hero_poster.jpg`, `hero.jpg`, other site assets, and all original app/sample files are unchanged. The old hero MP4 is preserved; its poster supplies the decorative background, while the new five-second mountain montage is the opening video. To change the opening demo later, update the source, poster, label and caption in `figure.hero-demo` in **both** HTML files. Mountain is also the first example below the stats; swap the two complete `figure.demo-card` blocks on both pages to change that order. No app default is controlled by this generator.

## Reproduce

Requires Python 3 and FFmpeg / ffprobe (generated with FFmpeg 9.0.1). From this repository:

```sh
python3 tools/make_panovi_demos.py \
  --mountain-dir "$HOME/Downloads/金時山DEMO候補" \
  --city-dir ../Panovi/Panovi/SampleVideos \
  --output-dir img
```

Use `--scene mountain` or `--scene city` to regenerate only one example. Change the `SCENES` start times in the script to choose another portion; each input must contain the full five-second range. The script rejects HDR inputs to prevent accidentally substituting the older HLG city recordings for the documented SDR copies.

| Scene | Input | Start (seconds) |
| --- | --- | ---: |
| Mountain | `left-panovi_944A428E_C2362D.MOV` | 2.03333333 |
| Mountain | `right-panovi_944A428E_30B6DB.MOV` | 2.10000000 |
| Mountain | `panovi_A64BFC22.mp4` | 2.00000000 |
| City | `demo_left.MOV` (6-second SDR app sample) | 0.53333333 |
| City | `demo_right.MOV` (6-second SDR app sample) | 0.60000000 |
| City | `demo_stitched.mp4` (4260 × 1264, 5.9 seconds) | 0.50000000 |

Mountain camera session: `944A428E`. City camera session: `05043199-1F72-424A-9E21-21FA3F200595`. Do not substitute the 10-second HDR city originals or the older 3798 × 1666 stitched result.

FFmpeg's automatic display rotation is intentionally enabled: the mountain left source carries a −180° display matrix. Frames are scaled with their full width and height; there is no content crop, warp, restitching or seam retouching. The different panorama aspect ratios are kept, so their lower panels have different heights. Source exposure differences and existing stitching artifacts remain as supplied.

Decoding/scaling is performed serially with software codecs and limited thread counts (1–2 per FFmpeg stage). It does not use the GPU, Simulator, or any app build. Intermediate FFV1 clips live in a temporary directory and are removed after rendering. The final clips are muted by removing audio tracks entirely. These files are web presentation assets; they do not preserve the calibration metadata required for in-app stitching.

## Timing evidence

Timing was checked independently for the two source sets, using the original audio before discarding it from the web files:

- Mountain: left-to-stitched cross-correlation peaks at −33 ms (0.917 correlation). Right-to-stitched has a weaker −90 ms peak. The nearest 30 fps boundaries used here are source left = result +1 frame and source right = result +3 frames. Source and result frames were also inspected for matching landscape and hiker positions.
- City: left-to-stitched peaks at −33 ms in three separate windows (0.879–0.907 correlation after 120–400 Hz filtering). Left-to-right peaks at +73 ms in the first 1.5-second window (0.505 correlation), and at the same lag over the complete range and a later window. This gives right ≈ result +106 ms; +3 frames / 100 ms is the nearest 30 fps boundary. Cross-camera audio correlation is weaker than the copied left/result audio; the montage is aligned to video-frame precision, not claimed to be sample-accurate.

## Page behavior and checks

The opening mountain demo uses a separate `object-fit:contain` frame so all three panels remain visible. At 980 px and wider it sits beside the existing headline and CTAs; on smaller screens it appears between the headline and details. Both lower examples remain visible. Neither the hero nor the examples section depends on `.rise`, JavaScript, or IntersectionObserver for visibility. Native controls provide play, pause, seeking and fullscreen. The videos have `preload="none"`, posters and descriptive labels; the examples also provide download links. No autoplay is added, including for reduced-motion users. The lower two-column layout becomes one column below 900 px. The decorative hero background is now a static image; existing band-video behavior is unchanged.

The generator checks dimensions, frame count, duration, codec, pixel format and absence of audio. Local verification also checked fast-start atom ordering, full decoding, the poster layouts and the new JP/EN file references. The Japanese desktop hero was visually inspected in Safari: the full three-panel frame, headline, caption and CTA fit without overlap. The browser automation connection was intermittent, so browser playback and mobile viewport behavior were not fully verified. The local review server was started at `http://127.0.0.1:4187/#examples` (English: `/en/#examples`).

## Publication

This is the static repository `git@github.com:starclipapp/panovi-site.git`, with `CNAME` set to `panovi.app` and `.nojekyll`. There is no build step or deployment workflow. The public site is served by GitHub Pages.

Publish reviewed changes through the existing `main` branch. After pushing, verify the public Japanese/English HTML and both MP4/poster files against the local files. Do not count a successful push alone as a completed deployment. `gh` was not installed on the development machine; the unauthenticated Pages API returned 404, so it cannot be used as deployment-status evidence here.
