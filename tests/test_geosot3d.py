"""Unit tests for tsdp.geosot3d."""
import math

import pytest

from tsdp.geosot3d import (
    Voxel, subdivide, parent, siblings,
    cell_diagonal_metres, encode, decode,
)


class TestVoxel:
    def test_cell_size_halves_per_level(self):
        v0 = Voxel(level=5, lon_idx=0, lat_idx=0)
        v1 = Voxel(level=6, lon_idx=0, lat_idx=0)
        assert v0.cell_size_deg() == pytest.approx(2 * v1.cell_size_deg())

    def test_bbox_is_square(self):
        v = Voxel(level=8, lon_idx=10, lat_idx=20)
        x0, y0, x1, y1 = v.bbox_deg()
        assert (x1 - x0) == pytest.approx(y1 - y0)


class TestSubdivide:
    def test_produces_four_children(self):
        v = Voxel(5, 3, 7)
        children = subdivide(v)
        assert len(children) == 4

    def test_children_are_one_level_deeper(self):
        v = Voxel(5, 3, 7)
        for c in subdivide(v):
            assert c.level == v.level + 1

    def test_children_indices_correct(self):
        v = Voxel(5, 3, 7)
        sw, se, nw, ne = subdivide(v)
        assert (sw.lon_idx, sw.lat_idx) == (6, 14)
        assert (se.lon_idx, se.lat_idx) == (7, 14)
        assert (nw.lon_idx, nw.lat_idx) == (6, 15)
        assert (ne.lon_idx, ne.lat_idx) == (7, 15)


class TestParentAndSiblings:
    def test_parent_inverts_subdivide(self):
        v = Voxel(5, 3, 7)
        for c in subdivide(v):
            assert parent(c) == v

    def test_siblings_includes_self(self):
        v = Voxel(5, 3, 7)
        for c in subdivide(v):
            assert c in siblings(c)

    def test_level_zero_has_no_parent(self):
        with pytest.raises(ValueError):
            parent(Voxel(0, 0, 0))


class TestCellDiagonal:
    def test_positive(self):
        v = Voxel(5, 100, 100)
        assert cell_diagonal_metres(v) > 0

    def test_smaller_at_higher_level(self):
        v_coarse = Voxel(5, 100, 100)
        v_fine = Voxel(7, 400, 400)  # ~ same physical region
        assert cell_diagonal_metres(v_fine) < cell_diagonal_metres(v_coarse)


class TestEncoding:
    @pytest.mark.parametrize("v", [
        Voxel(0, 0, 0),
        Voxel(5, 3, 7),
        Voxel(9, 100, 200),
        Voxel(15, 32000, 16000),
    ])
    def test_encode_decode_roundtrip(self, v):
        assert decode(encode(v)) == v

    def test_level_too_high_raises(self):
        with pytest.raises(ValueError):
            encode(Voxel(64, 0, 0))
