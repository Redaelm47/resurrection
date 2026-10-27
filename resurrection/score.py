"""How close the new app is to the old one, from 0 to 1.

- look: frame by frame SSIM between the source video and the new app;
- layout: IoU between components found on both sides, matched by type;
- journey: share of steps that land on the expected screen.

Until SAM 3.1 is plugged in, layout compares the boxes Muse Wonder read from
the video with the boxes the browser reports for the new app.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment
from skimage.io import imread
from skimage.metrics import structural_similarity

from .replay import Capture
from .spec import AppSpec

WEIGHTS = {"look": 0.4, "layout": 0.4, "journey": 0.2}


def ssim(a_path, b_path) -> float:
    a = imread(a_path, as_gray=True)
    b = imread(b_path, as_gray=True)
    if a.shape != b.shape:
        raise ValueError(f"size mismatch: {a.shape} vs {b.shape}")
    return float(structural_similarity(a, b, data_range=1.0))


def iou(a: list[float], b: list[float]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    union = aw * ah + bw * bh - inter
    return inter / union if union else 0.0


def match_iou(expected: list[list[float]], found: list[list[float]]) -> float:
    """Best one-to-one matching; missing or extra components count as 0."""
    if not expected and not found:
        return 1.0
    if not expected or not found:
        return 0.0
    m = np.array([[iou(e, f) for f in found] for e in expected])
    rows, cols = linear_sum_assignment(-m)
    return float(m[rows, cols].sum() / max(len(expected), len(found)))


def layout(spec: AppSpec, cap: Capture) -> float:
    screen = spec.screen(cap.expected_screen)
    scores = []
    for kind in {c.type for c in screen.components}:
        expected = [c.box for c in screen.components if c.type == kind]
        ids = {c.id for c in screen.components if c.type == kind}
        found = [box for cid, box in cap.app_boxes.items() if cid in ids]
        scores.append(match_iou(expected, found))
    return float(np.mean(scores)) if scores else 1.0


def report(spec: AppSpec, captures: list[Capture]) -> dict:
    steps = []
    for cap in captures:
        steps.append(
            {
                "step": cap.step,
                "screen": cap.expected_screen,
                "look": round(ssim(cap.source_frame, cap.app_frame), 3),
                "layout": round(layout(spec, cap), 3),
                "journey": 1.0 if cap.actual_screen == cap.expected_screen else 0.0,
            }
        )
    parts = {k: round(float(np.mean([s[k] for s in steps])), 3) for k in WEIGHTS}
    total = round(sum(WEIGHTS[k] * parts[k] for k in WEIGHTS), 3)
    return {"score": total, **parts, "steps": steps}
