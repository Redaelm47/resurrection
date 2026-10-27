"""Model providers, one interface per step of the pipeline.

Each Meta model sits behind a small interface so the pipeline runs end to end
today with offline stand-ins, and the real model is plugged in by swapping
one class.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .spec import AppSpec
from .template import render_html


class VideoReader(Protocol):
    """Video of the old app -> AppSpec. Target model: Muse Wonder."""

    def extract(self, video: Path) -> AppSpec: ...


class CodeWriter(Protocol):
    """AppSpec (+ score report) -> index.html. Target model: Muse Code."""

    def write(self, spec: AppSpec, report: dict | None = None) -> str: ...


class ImageMaker(Protocol):
    """Pixelated or missing visuals -> clean PNG. Target model: Muse Image."""

    def make(self, prompt: str, reference: Path | None, out: Path) -> Path: ...


class Segmenter(Protocol):
    """Frame -> boxes per label ("button", "text field", "image"). Target model: SAM 3.1."""

    def boxes(self, image: Path, labels: list[str]) -> dict[str, list[list[int]]]: ...


# Offline stand-ins, used until the Meta models are plugged in.


class SpecFileReader:
    """Reads a hand-written spec next to the video (my-app.mp4 -> my-app.json)."""

    def extract(self, video: Path) -> AppSpec:
        return AppSpec.load(video.with_suffix(".json"))


class TemplateWriter:
    """Deterministic baseline: draws every component at its box. Ignores the report."""

    def write(self, spec: AppSpec, report: dict | None = None) -> str:
        return render_html(spec)


# Meta models. Fill these in once the API access is set up.


class MuseWonderReader:
    def extract(self, video: Path) -> AppSpec:
        raise NotImplementedError("Muse Wonder: send the video, ask for JSON matching spec.py")


class MuseCodeWriter:
    def write(self, spec: AppSpec, report: dict | None = None) -> str:
        raise NotImplementedError("Muse Code: send the spec (and the last report), get index.html back")


class MuseImageMaker:
    def make(self, prompt: str, reference: Path | None, out: Path) -> Path:
        raise NotImplementedError("Muse Image: redraw the asset from the reference crop")


class Sam31Segmenter:
    def boxes(self, image: Path, labels: list[str]) -> dict[str, list[list[int]]]:
        raise NotImplementedError("SAM 3.1: text-prompted segmentation, one prompt per label")


READERS = {"spec-file": SpecFileReader, "muse-wonder": MuseWonderReader}
WRITERS = {"template": TemplateWriter, "muse-code": MuseCodeWriter}
