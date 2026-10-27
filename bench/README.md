# Resurrection Bench

How well does a system turn a video of an old website back into a working one? This benchmark answers with a number, using ground truth the system never sees.

## Tasks

Each task is a real 1999 website, archived by the [Internet Archive's Wayback Machine](https://web.archive.org/), and a short visit: a start page and two clicks.

| Task | Site | Visit |
|---|---|---|
| `nasa-1999` | nasa.gov, January 1999 | home, Multimedia Gallery, Video Gallery |
| `fema-1999` | fema.gov, January 1999 | home, FEMA for Kids, Main Icons |
| `noaa-1999` | noaa.gov, January 1999 | home, Explore NOAA, NOAA History |

We picked US federal government sites because their content is in the public domain, so we can share the captures. Broken images in the archive are kept as they are: a real video of an old app has them too.

## How a task was captured

The visits were done by hand in Chrome on the archived pages (Wayback `if_` mode, no toolbar), viewport 1470x706. After each step we saved:

- `truth_XX.jpg`: a screenshot of the page;
- `step_XX.json`: where the click landed, and the boxes of the page's real links, images, buttons and fields, read from the live DOM.

`resurrect bench assemble` turns these into `truth.json` and `video.mp4`, the replay of the visit with a moving cursor. **The video is the only input a system gets.**

## How an entry is scored

An entry is `bench/entries/<system>/<task>/index.html` (plus its assets). It is a black box: we open it in Chromium at 1470x706, click at the same coordinates as in the video, and compare every step to the ground truth.

| Metric | Weight | What it measures |
|---|---|---|
| Look | 40 % | pixel similarity (SSIM) with the real page, rescaled so a blank page scores 0 and a perfect copy 1 |
| Layout | 40 % | are the real links, images, buttons and fields there, at the same place and size (IoU, matched by type) |
| Journey | 20 % | does each click open the right page (closest real page, and at least 50 % look) |

Two baselines keep the numbers honest:

- **blank**: an empty page;
- **screenshot**: the first video frame pasted as one image. It looks right until the first click, then nothing works and it has no real elements.

```bash
resurrect bench assemble   # captures -> truth.json + video.mp4
resurrect bench run        # baselines + every entry -> out/bench/results.md
```

## Rules for entries

- Input: `video.mp4` only. Reading `truth*`, `step_*` or the archived site is cheating.
- Images may be cropped from the video frames (a restoration model like Muse Image can redraw them).
- No full-screen screenshot pasted as one image.

## Results

| System | fema-1999 | nasa-1999 | noaa-1999 | Look | Layout | Journey | **Score** |
|---|---|---|---|---|---|---|---|
| blank | 0% | 0% | 0% | 0% | 0% | 0% | **0%** |
| screenshot | 20% | 19% | 20% | 32% | 1% | 33% | **20%** |
| claude-code | 75% | 81% | 80% | 82% | 65% | 100% | **79%** |

First results (Oct 27, 2026). `claude-code` is Claude Code standing in for the Meta models while we save API credits: it got only the video, cropped images from its frames and wrote the pages. Meta model entries come next.

![Original (left) and resurrected (right)](side-by-side.jpg)

## Known limits

- Three tasks, two clicks each: a first version, to be extended.
- The browser extension used for the captures left its pointer in some screenshots; it costs every system the same few pixels.
- Layout uses DOM boxes of the new app. It cannot judge an app drawn on a canvas; SAM 3.1 on pixels will cover that case.
