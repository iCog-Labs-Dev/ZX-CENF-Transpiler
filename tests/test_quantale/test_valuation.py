"""Tests for valuation.py."""

from __future__ import annotations

from dataclasses import dataclass

import pyzx as zx
import pytest

from zx_cenf.quantale.algebra import top
from zx_cenf.quantale.valuation import (
    COORDINATE_NAMES,
    DIM,
    mu_from_pyzx_graph,
    mu_from_run_result,
    sentinel_for_failed_extraction,
)


def _reduced_graph(seed: int):
    
    g = zx.generate.cliffordT(
        3,
        20,
        p_t=0.25,
        p_s=0.1,
        p_hsh=0.2,
        p_cnot=0.3,
        seed=seed,
    )
    zx.simplify.full_reduce(g, quiet=True)
    return g


@dataclass
class _FakeOrderingRunResult:
    

    twoqubitcount: int | None
    tcount: int | None
    depth: int | None
    extraction_failed: bool


def test_coordinate_dimension_is_three():
    assert DIM == 3
    assert COORDINATE_NAMES == (
        "twoqubitcount",
        "tcount",
        "depth",
    )


def test_mu_from_run_result_normal_case():
    run = _FakeOrderingRunResult(
        twoqubitcount=9,
        tcount=4,
        depth=19,
        extraction_failed=False,
    )

    value = mu_from_run_result(run)

    assert value is not None
    assert value.coords == (9.0, 4.0, 19.0)
    assert value.dim == DIM
    assert value.is_finite()


def test_mu_from_run_result_preserves_zero_costs():
    
    run = _FakeOrderingRunResult(
        twoqubitcount=0,
        tcount=0,
        depth=0,
        extraction_failed=False,
    )

    value = mu_from_run_result(run)

    assert value is not None
    assert value.coords == (0.0, 0.0, 0.0)


def test_mu_from_run_result_returns_none_on_extraction_failure():
    run = _FakeOrderingRunResult(
        twoqubitcount=None,
        tcount=None,
        depth=None,
        extraction_failed=True,
    )

    assert mu_from_run_result(run) is None


def test_extraction_failure_does_not_create_fake_valuation():
    
    run = _FakeOrderingRunResult(
        twoqubitcount=None,
        tcount=None,
        depth=None,
        extraction_failed=True,
    )

    value = mu_from_run_result(run)

    assert value is None


def test_mu_from_pyzx_graph_returns_three_coordinates():
    g = _reduced_graph(seed=42)

    value = mu_from_pyzx_graph(g)

    assert value.dim == DIM
    assert len(value.coords) == 3
    assert value.is_finite()


def test_mu_from_pyzx_graph_coordinates_match_circuit_stats():
    g = _reduced_graph(seed=42)

    circuit = zx.extract_circuit(g.copy(), quiet=True)
    value = mu_from_pyzx_graph(g, circuit=circuit)

    assert value.coords[0] == float(circuit.twoqubitcount())
    assert value.coords[1] == float(circuit.tcount())
    assert value.coords[2] == float(circuit.depth())


def test_mu_from_pyzx_graph_extracts_circuit_when_not_supplied():
    g = _reduced_graph(seed=42)

    value = mu_from_pyzx_graph(g)
    circuit = zx.extract_circuit(g.copy(), quiet=True)

    assert value.coords == (
        float(circuit.twoqubitcount()),
        float(circuit.tcount()),
        float(circuit.depth()),
    )


def test_mu_from_pyzx_graph_raises_when_extraction_fails():
    
    g = zx.Graph()
    g.add_vertex(zx.VertexType.Z)

    with pytest.raises(Exception):
        mu_from_pyzx_graph(g)


def test_sentinel_has_correct_dimension():
    sentinel = sentinel_for_failed_extraction()

    assert sentinel.dim == DIM
    assert sentinel.coords == top(DIM).coords


def test_sentinel_is_positive_infinity_in_all_coordinates():
    sentinel = sentinel_for_failed_extraction()

    assert sentinel.coords == (
        float("inf"),
        float("inf"),
        float("inf"),
    )
    assert not sentinel.is_finite()


def test_every_finite_valuation_is_below_failed_extraction_sentinel():
    sentinel = sentinel_for_failed_extraction()
    ordinary = mu_from_pyzx_graph(_reduced_graph(seed=1))

    assert ordinary <= sentinel
    assert not sentinel <= ordinary
    assert not sentinel.dominates(ordinary)


def test_valuation_dimension_matches_coordinate_names():
    value = mu_from_run_result(
        _FakeOrderingRunResult(
            twoqubitcount=5,
            tcount=2,
            depth=7,
            extraction_failed=False,
        )
    )

    assert value is not None
    assert value.dim == len(COORDINATE_NAMES)
    assert value.dim == DIM