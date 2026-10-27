"""End to end on the example app: film it, then resurrect it from the video."""

import shutil
from pathlib import Path

from resurrection.loop import resurrect
from resurrection.providers import SpecFileReader, TemplateWriter
from resurrection.replay import film
from resurrection.spec import AppSpec
from resurrection.template import render_html

EXAMPLE = Path(__file__).parent.parent / "examples" / "robot-club.json"


def test_baseline_matches_its_own_video(tmp_path):
    spec = AppSpec.load(EXAMPLE)
    app = tmp_path / "original.html"
    app.write_text(render_html(spec))
    video = film(app, spec, tmp_path / "robot-club.mp4")
    shutil.copy(EXAMPLE, video.with_suffix(".json"))

    result = resurrect(video, SpecFileReader(), TemplateWriter(), tmp_path / "out", max_rounds=1)

    assert result["journey"] == 1.0
    assert result["layout"] == 1.0
    assert result["look"] > 0.9
