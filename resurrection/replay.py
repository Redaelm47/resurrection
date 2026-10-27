"""Redo the clicks of the source video on the new app and capture both sides.

For every step of the journey we keep two images: the source video frame once
the step has settled, and a screenshot of the new app after the same action.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from playwright.sync_api import sync_playwright

from .spec import AppSpec

SETTLE = 0.5  # seconds after an action before the source frame is taken


@dataclass
class Capture:
    step: int
    expected_screen: str
    actual_screen: str
    source_frame: Path
    app_frame: Path
    app_boxes: dict[str, list[int]]  # component id -> [x, y, w, h] in the new app


def dump_frames(video: Path, out: Path, every: float = 0.5) -> list[Path]:
    """Frames every `every` seconds, named by timestamp, so someone (or Claude Code) can read the video."""
    out.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video))
    duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / (cap.get(cv2.CAP_PROP_FPS) or 1)
    paths, t = [], 0.0
    while t < duration:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            break
        path = out / f"t{t:06.2f}.png"
        cv2.imwrite(str(path), frame)
        paths.append(path)
        t += every
    cap.release()
    return paths


def source_frames(video: Path, spec: AppSpec, out: Path) -> list[Path]:
    """One frame per step, taken SETTLE seconds after the step (or just before the next one)."""
    out.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video))
    paths = []
    for i, step in enumerate(spec.journey):
        t = step.t + SETTLE
        if i + 1 < len(spec.journey):
            t = min(t, spec.journey[i + 1].t - 0.05)
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            raise ValueError(f"no frame at {t:.2f}s in {video}")
        frame = cv2.resize(frame, tuple(spec.viewport))
        path = out / f"source_{i:02d}.png"
        cv2.imwrite(str(path), frame)
        paths.append(path)
    cap.release()
    return paths


def _act(page, action: dict | None) -> None:
    if not action:
        return
    target = page.locator(f'[data-id="{action["target"]}"]')
    if action["type"] == "click":
        target.click()
    elif action["type"] == "type":
        target.fill(action.get("text", ""))


def film(app: Path, spec: AppSpec, video: Path, fps: int = 10) -> Path:
    """Play the journey on an HTML app and save it as a video (self-checks and demos)."""
    w, h = spec.viewport
    end = spec.journey[-1].t + 2 * SETTLE
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(app.resolve().as_uri())
        frame, step = 0, 0
        while frame / fps < end:
            while step < len(spec.journey) and spec.journey[step].t <= frame / fps:
                _act(page, spec.journey[step].action)
                step += 1
            png = page.screenshot()
            writer.write(cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR))
            frame += 1
        browser.close()
    writer.release()
    return video


def replay(app: Path, spec: AppSpec, video: Path, out: Path) -> list[Capture]:
    sources = source_frames(video, spec, out)
    w, h = spec.viewport
    captures = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(app.resolve().as_uri())
        for i, step in enumerate(spec.journey):
            _act(page, step.action)
            page.wait_for_timeout(SETTLE * 1000)
            shot = out / f"app_{i:02d}.png"
            page.screenshot(path=str(shot))
            boxes = page.evaluate(
                """() => Object.fromEntries([...document.querySelectorAll('[data-id]')]
                    .filter(el => el.offsetParent !== null)
                    .map(el => { const r = el.getBoundingClientRect();
                                 return [el.dataset.id, [r.x, r.y, r.width, r.height].map(Math.round)]; }))"""
            )
            captures.append(
                Capture(i, step.screen, page.evaluate("document.body.dataset.screen"), sources[i], shot, boxes)
            )
        browser.close()
    return captures
