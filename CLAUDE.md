# Working on Resurrection with Claude Code

To save the Meta API credits, Claude Code plays the role of the Meta models for now. The pipeline code stays the same; only who writes the spec and the app changes. Meta models get plugged in later through `resurrection/providers.py`.

| Step | Later (Meta) | Now (Claude Code) |
|---|---|---|
| Video to spec | Muse Wonder | Claude Code reads the frames and writes `spec.json` |
| Spec to app, fixes | Muse Code | Claude Code writes `index.html`, then fixes it from `report.json` |
| Visuals | Muse Image | placeholders (plain colors) |
| Layout judge | SAM 3.1 | DOM boxes vs spec boxes (already in `score.py`) |

## Procedure for one video

1. `resurrect frames samples/<name>.mp4 --every 0.5` and look at the frames in `out/<name>/frames/` (file names are timestamps).
2. Write `out/<name>/spec.json` following `resurrection/spec.py` and `examples/robot-club.json`. Boxes are in video pixels; `viewport` is the video size; each journey step has the time of the action.
3. Write `out/<name>/index.html`. Keep the contract: every component has `data-id` from the spec, and `<body data-screen>` names the visible screen.
4. `resurrect score samples/<name>.mp4 out/<name>/spec.json out/<name>/index.html`
5. Read `report.json`, fix the weakest steps, score again. Stop at 90 % or after 5 rounds, and keep each round's score for the demo.

## Rules

- Hackathon rules: public repo, all code written during the event (Oct 27 to Nov 4, 2026), no code or assets we have no rights to.
- Only resurrect apps we have the rights to (see `samples/README.md`). Videos are never committed.
- English in the repo (judges read it).
- Run `pytest` before pushing.
