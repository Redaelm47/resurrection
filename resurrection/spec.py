"""The app spec: what the video shows, as structured JSON.

Muse Wonder writes it from the video, Muse Code turns it into a web app,
and the replay uses its journey to redo the same clicks.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

COMPONENT_TYPES = ("button", "text_field", "image", "text", "link")


@dataclass
class Component:
    id: str
    type: str  # one of COMPONENT_TYPES
    box: list[int]  # [x, y, width, height] in video pixels
    text: str = ""
    goto: str | None = None  # screen opened when clicked
    style: dict = field(default_factory=dict)


@dataclass
class Screen:
    id: str
    title: str = ""
    background: str = "#ffffff"
    components: list[Component] = field(default_factory=list)


@dataclass
class Step:
    t: float  # seconds in the source video
    screen: str  # screen visible once the step is done
    action: dict | None = None  # {"type": "click" | "type", "target": id, "text": ...}


@dataclass
class AppSpec:
    name: str
    viewport: list[int]  # [width, height] of the source video
    screens: list[Screen]
    journey: list[Step]

    def screen(self, screen_id: str) -> Screen:
        return next(s for s in self.screens if s.id == screen_id)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(self.to_json() + "\n")

    @classmethod
    def from_dict(cls, data: dict) -> AppSpec:
        screens = [
            Screen(**{**s, "components": [Component(**c) for c in s.get("components", [])]})
            for s in data["screens"]
        ]
        return cls(
            name=data["name"],
            viewport=data["viewport"],
            screens=screens,
            journey=[Step(**s) for s in data["journey"]],
        )

    @classmethod
    def load(cls, path: str | Path) -> AppSpec:
        return cls.from_dict(json.loads(Path(path).read_text()))
