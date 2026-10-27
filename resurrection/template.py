"""Baseline HTML for a spec, and the contract every generated app must follow.

Contract (the replay relies on it, so Muse Code must keep it too):
- each component carries data-id="<component id>";
- <body data-screen="<screen id>"> always names the visible screen.
"""

from __future__ import annotations

from html import escape

from .spec import AppSpec, Component, Screen

TAGS = {"button": "button", "text_field": "input", "image": "div", "text": "div", "link": "a"}


def _style(c: Component) -> str:
    x, y, w, h = c.box
    rules = {"left": f"{x}px", "top": f"{y}px", "width": f"{w}px", "height": f"{h}px", **c.style}
    return ";".join(f"{k}:{v}" for k, v in rules.items())


def _component(c: Component) -> str:
    tag = TAGS.get(c.type, "div")
    attrs = f'data-id="{escape(c.id)}" class="{c.type}" style="{escape(_style(c))}"'
    if c.goto:
        attrs += f' data-goto="{escape(c.goto)}"'
    if tag == "input":
        return f'<input {attrs} placeholder="{escape(c.text)}">'
    return f"<{tag} {attrs}>{escape(c.text)}</{tag}>"


def _screen(s: Screen) -> str:
    inner = "\n    ".join(_component(c) for c in s.components)
    return f'<section data-screen="{escape(s.id)}" style="background:{escape(s.background)}">\n    {inner}\n  </section>'


def render_html(spec: AppSpec) -> str:
    w, h = spec.viewport
    screens = "\n  ".join(_screen(s) for s in spec.screens)
    first = spec.journey[0].screen if spec.journey else spec.screens[0].id
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{escape(spec.name)}</title>
<style>
  html, body {{ margin: 0; width: {w}px; height: {h}px; overflow: hidden; font: 14px Verdana, sans-serif; }}
  section {{ position: absolute; inset: 0; display: none; }}
  section > * {{ position: absolute; box-sizing: border-box; margin: 0; }}
  .image {{ background: #ccc center / cover no-repeat; }}
</style>
</head>
<body data-screen="{escape(first)}">
  {screens}
<script>
  const show = id => {{
    document.body.dataset.screen = id;
    document.querySelectorAll("section").forEach(s => s.style.display = s.dataset.screen === id ? "block" : "none");
  }};
  document.addEventListener("click", e => {{
    const el = e.target.closest("[data-goto]");
    if (el) {{ e.preventDefault(); show(el.dataset.goto); }}
  }});
  show(document.body.dataset.screen);
</script>
</body>
</html>
"""
