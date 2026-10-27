"""The benchmark must give nothing to an empty page and everything to the real page."""

from pathlib import Path

from resurrection.bench import assemble, baseline, evaluate, layout_score

TASK = Path(__file__).parent.parent / "bench" / "data" / "nasa-1999"


def test_layout_counts_missing_and_extra_kinds():
    truth = {"link": [[0, 0, 10, 10]], "image": [], "button": [], "field": []}
    assert layout_score(truth, truth) == 1.0
    assert layout_score(truth, {"link": [], "image": [[0, 0, 5, 5]]}) == 0.0


def test_blank_page_scores_zero(tmp_path):
    assemble(TASK)
    result = evaluate(TASK, baseline("blank", TASK, tmp_path), tmp_path)
    assert result["score"] == 0.0
