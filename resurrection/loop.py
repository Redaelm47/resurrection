"""The agent loop: read the video, write the app, replay, score, fix, repeat."""

from __future__ import annotations

import json
from pathlib import Path

from .providers import CodeWriter, VideoReader
from .replay import replay
from .score import report


def resurrect(
    video: Path,
    reader: VideoReader,
    writer: CodeWriter,
    out: Path,
    threshold: float = 0.9,
    max_rounds: int = 5,
) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    spec = reader.extract(video)
    spec.save(out / "spec.json")

    last = None
    for round_ in range(1, max_rounds + 1):
        rdir = out / f"round_{round_}"
        rdir.mkdir(exist_ok=True)
        app = rdir / "index.html"
        app.write_text(writer.write(spec, last))
        last = report(spec, replay(app, spec, video, rdir))
        (rdir / "report.json").write_text(json.dumps(last, indent=2) + "\n")
        print(f"round {round_}: score {last['score']:.0%} "
              f"(look {last['look']:.0%}, layout {last['layout']:.0%}, journey {last['journey']:.0%})")
        if last["score"] >= threshold:
            break
    return last
