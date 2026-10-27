"""Resurrection Bench: score any system that turns a video of an old site into a web app.

A task is an archived site and a few clicks on it, captured in a real browser:
one screenshot per step, where each click landed, and the boxes of the real
links, buttons, fields and images. `assemble` turns that ground truth into the
video. A system only ever gets the video. `evaluate`
treats its index.html as a black box: same clicks at the same coordinates,
then look (SSIM), layout (IoU against the real elements) and journey (does
each click open the right page).
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
from playwright.sync_api import sync_playwright

from .score import WEIGHTS, match_iou, ssim

FPS = 10
HOLD = 1.5  # seconds a page stays on screen before the next action
MOVE = 0.6  # seconds the cursor takes to reach its target
JOURNEY_MIN = 0.5  # a click only counts if the new screen looks at least this much like the right page

# Same element classes on both sides, read from the live DOM.
ELEMENTS_JS = """() => {
  const kinds = {
    link: 'a[href]',
    image: 'img, input[type=image]',
    button: 'button, input[type=submit], input[type=button], input[type=reset]',
    field: 'textarea, select, input:not([type]), input[type=text], input[type=search], input[type=password], input[type=email]',
  };
  const W = innerWidth, H = innerHeight, out = {};
  for (const [kind, sel] of Object.entries(kinds)) {
    out[kind] = [...document.querySelectorAll(sel)].map(el => el.getBoundingClientRect())
      .filter(r => r.width >= 4 && r.height >= 4 && r.right > 0 && r.bottom > 0 && r.left < W && r.top < H)
      .map(r => [r.x, r.y, r.width, r.height].map(Math.round));
  }
  return out;
}"""


def _cursor(frame: np.ndarray, x: float, y: float) -> np.ndarray:
    """Classic arrow pointer, so the video shows what gets clicked."""
    tip = np.array([[0, 0], [0, 17], [4, 13], [7, 20], [10, 19], [7, 12], [12, 12]], np.int32)
    pts = (tip + [int(x), int(y)]).reshape(-1, 1, 2)
    out = frame.copy()
    cv2.fillPoly(out, [pts], (255, 255, 255))
    cv2.polylines(out, [pts], True, (0, 0, 0), 1, cv2.LINE_AA)
    return out


def assemble(task_dir: Path) -> Path:
    """Turn the captured steps (step_XX.json + truth_XX.jpg) into truth.json and video.mp4.

    The captures come from a real browser session on the archived pages: a
    screenshot after each click, where the click landed, and the boxes of the
    page's real elements. The video replays them with a moving cursor.
    """
    steps = [json.loads(f.read_text()) for f in sorted(task_dir.glob("step_*.json"))]
    w, h = steps[0]["w"], steps[0]["h"]
    if any((s["w"], s["h"]) != (w, h) for s in steps):
        raise ValueError(f"{task_dir.name}: every capture must have the same viewport")
    frames = []
    for i in range(len(steps)):
        frame = cv2.imread(str(task_dir / f"truth_{i:02d}.jpg"))
        frame = cv2.resize(frame, (w, h))
        cv2.imwrite(str(task_dir / f"truth_{i:02d}.png"), frame)
        frames.append(frame)

    writer = cv2.VideoWriter(str(task_dir / "video.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (w, h))
    t, mouse, truth_steps = 0.0, (w * 0.6, h * 0.7), []
    for i, step in enumerate(steps):
        a = step["action"]
        if a:
            n = round(MOVE * FPS)
            for k in range(1, n + 1):
                f = k / n
                at = (mouse[0] + (a["x"] - mouse[0]) * f, mouse[1] + (a["y"] - mouse[1]) * f)
                writer.write(_cursor(frames[i - 1], *at))
                t += 1 / FPS
            mouse = (a["x"], a["y"])
        truth_steps.append({"t": round(t, 2), "action": a, "page": step["url"], "elements": step["elements"]})
        for _ in range(round(HOLD * FPS)):
            writer.write(_cursor(frames[i], *mouse))
            t += 1 / FPS
    writer.release()

    truth = {"id": task_dir.name, "url": steps[0]["url"], "viewport": [w, h], "steps": truth_steps}
    (task_dir / "truth.json").write_text(json.dumps(truth, indent=2) + "\n")
    return task_dir / "video.mp4"


def _page_ids(truth: dict) -> list[int]:
    seen: dict[str, int] = {}
    return [seen.setdefault(s["page"], len(seen)) for s in truth["steps"]]


def layout_score(expected: dict, found: dict) -> float:
    kinds = [k for k in expected if expected[k] or found.get(k)]
    return float(np.mean([match_iou(expected[k], found.get(k, [])) for k in kinds])) if kinds else 1.0


def _look(truth_shot: Path, blank_sim: float, shot: Path) -> float:
    """SSIM rescaled so a blank white page scores 0 and a perfect copy 1.

    Raw SSIM is generous on the large flat areas of old sites (a blank page
    already gets 0.65 to 0.9), so we only count what a system adds over blank.
    """
    return max(0.0, (ssim(truth_shot, shot) - blank_sim) / (1 - blank_sim))


def evaluate(task_dir: Path, app: Path, out: Path) -> dict:
    truth = json.loads((task_dir / "truth.json").read_text())
    w, h = truth["viewport"]
    out.mkdir(parents=True, exist_ok=True)
    pages = _page_ids(truth)
    truth_shots = [task_dir / f"truth_{i:02d}.png" for i in range(len(truth["steps"]))]
    white = out / "white.png"
    cv2.imwrite(str(white), np.full((h, w, 3), 255, np.uint8))
    blank_sims = [ssim(t, white) for t in truth_shots]
    rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(app.resolve().as_uri(), wait_until="load")
        for i, step in enumerate(truth["steps"]):
            a = step["action"]
            if a:
                page.mouse.click(a["x"], a["y"])
                if a["type"] == "type":
                    page.keyboard.type(a["text"])
                try:
                    page.wait_for_load_state("load", timeout=5000)
                except Exception:
                    pass
            page.wait_for_timeout(300)
            shot = out / f"app_{i:02d}.png"
            page.screenshot(path=str(shot))
            looks = [_look(t, b, shot) for t, b in zip(truth_shots, blank_sims)]
            best = int(np.argmax(looks))
            rows.append({
                "step": i,
                "look": round(looks[i], 3),
                "layout": round(layout_score(step["elements"], page.evaluate(ELEMENTS_JS)), 3),
                "journey": 1.0 if pages[best] == pages[i] and looks[best] >= JOURNEY_MIN else 0.0,
            })
        browser.close()
    parts = {k: round(float(np.mean([r[k] for r in rows])), 3) for k in WEIGHTS}
    result = {"task": truth["id"], "score": round(sum(WEIGHTS[k] * parts[k] for k in WEIGHTS), 3), **parts,
              "steps": rows}
    (out / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


# Reference points: a system has to beat these to mean anything.


def baseline(kind: str, task_dir: Path, out: Path) -> Path:
    truth = json.loads((task_dir / "truth.json").read_text())
    w, h = truth["viewport"]
    out.mkdir(parents=True, exist_ok=True)
    body = ""
    if kind == "screenshot":  # the first video frame pasted as a flat image
        cap = cv2.VideoCapture(str(task_dir / "video.mp4"))
        ok, frame = cap.read()
        cap.release()
        cv2.imwrite(str(out / "frame.png"), frame)
        body = f'<img src="frame.png" width="{w}" height="{h}" style="display:block">'
    app = out / "index.html"
    app.write_text(f"<!doctype html><html><body style='margin:0'>{body}</body></html>\n")
    return app


def run(tasks: list[Path], entries: Path, out: Path) -> str:
    """Score the baselines and every entries/<system>/<task>/index.html, as a Markdown table."""
    systems = {name: lambda d, o, name=name: baseline(name, d, o) for name in ("blank", "screenshot")}
    for sys_dir in sorted(p for p in entries.glob("*") if p.is_dir()):
        systems[sys_dir.name] = lambda d, o, sys_dir=sys_dir: sys_dir / d.name / "index.html"

    results = {}
    for name, make in systems.items():
        for d in tasks:
            app = make(d, out / name / d.name)
            if app.exists():
                results[(name, d.name)] = evaluate(d, app, out / name / d.name)
    (out / "results.json").write_text(json.dumps({f"{s}/{t}": r for (s, t), r in results.items()}, indent=2) + "\n")

    head = "| System | " + " | ".join(d.name for d in tasks) + " | Look | Layout | Journey | **Score** |"
    lines = [head, "|" + "---|" * (len(tasks) + 5)]
    for name in systems:
        rows = [results[(name, d.name)] for d in tasks if (name, d.name) in results]
        if not rows:
            continue
        cells = [f"{results[(name, d.name)]['score']:.0%}" if (name, d.name) in results else "-" for d in tasks]
        mean = {k: np.mean([r[k] for r in rows]) for k in ("look", "layout", "journey", "score")}
        lines.append(f"| {name} | " + " | ".join(cells)
                     + f" | {mean['look']:.0%} | {mean['layout']:.0%} | {mean['journey']:.0%} | **{mean['score']:.0%}** |")
    table = "\n".join(lines)
    (out / "results.md").write_text(table + "\n")
    return table
