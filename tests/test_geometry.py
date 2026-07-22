"""Unit tests for pure geometry helpers in DFN engine."""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zdem_dfn.engine import point_to_segment_distance, _compute_outcode, INSIDE, LEFT, RIGHT


def test_point_on_segment_is_zero():
    d = point_to_segment_distance(1.0, 1.0, 0.0, 0.0, 2.0, 2.0)
    assert d < 1e-9


def test_point_near_midpoint():
    d = point_to_segment_distance(0.0, 1.0, 0.0, 0.0, 2.0, 0.0)
    assert abs(d - 1.0) < 1e-9


def test_point_beyond_endpoint_uses_endpoint():
    d = point_to_segment_distance(3.0, 0.0, 0.0, 0.0, 2.0, 0.0)
    assert abs(d - 1.0) < 1e-9


def test_degenerate_segment_is_point_distance():
    d = point_to_segment_distance(3.0, 4.0, 0.0, 0.0, 0.0, 0.0)
    assert abs(d - 5.0) < 1e-9


def test_outcode_inside_and_sides():
    assert _compute_outcode(5.0, 5.0, 0.0, 10.0, 0.0, 10.0) == INSIDE
    assert _compute_outcode(-1.0, 5.0, 0.0, 10.0, 0.0, 10.0) & LEFT
    assert _compute_outcode(11.0, 5.0, 0.0, 10.0, 0.0, 10.0) & RIGHT
