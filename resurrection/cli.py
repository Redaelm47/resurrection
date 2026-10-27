from __future__ import annotations

import argparse
import json
from pathlib import Path

from .loop import resurrect
from .providers import READERS, WRITERS
from .replay import dump_frames, film, replay
from .score import report
from .spec import AppSpec
from .template import render_html


def main() -> None:
    parser = argparse.ArgumentParser(prog="resurrect", description="Bring an old app back from a video of it.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="video -> working web app, scored against the video")
    run.add_argument("video", type=Path)
    run.add_argument("--reader", choices=READERS, default="spec-file")
    run.add_argument("--writer", choices=WRITERS, default="template")
    run.add_argument("--out", type=Path, default=Path("out"))
    run.add_argument("--threshold", type=float, default=0.9)
    run.add_argument("--max-rounds", type=int, default=5)

    frames = sub.add_parser("frames", help="dump video frames named by timestamp")
    frames.add_argument("video", type=Path)
    frames.add_argument("--every", type=float, default=0.5, help="seconds between frames")
    frames.add_argument("--out", type=Path, default=None)

    score = sub.add_parser("score", help="replay a spec's journey on an app and score it against the video")
    score.add_argument("video", type=Path)
    score.add_argument("spec", type=Path)
    score.add_argument("app", type=Path)
    score.add_argument("--out", type=Path, default=None)

    build = sub.add_parser("build", help="spec -> baseline index.html")
    build.add_argument("spec", type=Path)
    build.add_argument("--out", type=Path, default=Path("out/index.html"))

    rec = sub.add_parser("film", help="play a spec's journey on an HTML app and save the video")
    rec.add_argument("spec", type=Path)
    rec.add_argument("app", type=Path)
    rec.add_argument("video", type=Path)

    args = parser.parse_args()
    if args.cmd == "run":
        resurrect(args.video, READERS[args.reader](), WRITERS[args.writer](), args.out / args.video.stem,
                  args.threshold, args.max_rounds)
    elif args.cmd == "frames":
        out = args.out or Path("out") / args.video.stem / "frames"
        print(f"{len(dump_frames(args.video, out, args.every))} frames in {out}")
    elif args.cmd == "score":
        out = args.out or args.app.parent / "score"
        out.mkdir(parents=True, exist_ok=True)
        spec = AppSpec.load(args.spec)
        result = report(spec, replay(args.app, spec, args.video, out))
        (out / "report.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
    elif args.cmd == "build":
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(render_html(AppSpec.load(args.spec)))
        print(args.out)
    elif args.cmd == "film":
        print(film(args.app, AppSpec.load(args.spec), args.video))


if __name__ == "__main__":
    main()
