from resurrection.score import iou, match_iou


def test_iou_same_box():
    assert iou([0, 0, 10, 10], [0, 0, 10, 10]) == 1.0


def test_iou_half_overlap():
    assert round(iou([0, 0, 10, 10], [5, 0, 10, 10]), 3) == round(50 / 150, 3)


def test_iou_disjoint():
    assert iou([0, 0, 10, 10], [20, 20, 5, 5]) == 0.0


def test_match_ignores_order_and_counts_missing():
    a = [[0, 0, 10, 10], [50, 50, 10, 10]]
    assert match_iou(a, list(reversed(a))) == 1.0
    assert match_iou(a, a[:1]) == 0.5
