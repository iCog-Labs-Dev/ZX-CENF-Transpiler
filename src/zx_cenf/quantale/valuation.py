"""Map PyZX circuit measurements to QuantaleValue."""

from __future__ import annotations

from zx_cenf.quantale.algebra import QuantaleValue, top


COORDINATE_NAMES = ("twoqubitcount", "tcount", "depth")
DIM = len(COORDINATE_NAMES)


def mu_from_run_result(run_result) -> QuantaleValue | None:
    """Build a valuation from a Track 1 run result."""
    if run_result.extraction_failed:
        return None

    return QuantaleValue(
        (
            float(run_result.twoqubitcount),
            float(run_result.tcount),
            float(run_result.depth),
        )
    )


def mu_from_pyzx_graph(g, circuit=None) -> QuantaleValue:
    """Build a valuation from a PyZX graph or extracted circuit."""
    import pyzx as zx

    if circuit is None:
        circuit = zx.extract_circuit(g.copy(), quiet=True)

    return QuantaleValue(
        (
            float(circuit.twoqubitcount()),
            float(circuit.tcount()),
            float(circuit.depth()),
        )
    )


def sentinel_for_failed_extraction() -> QuantaleValue:
    """Return the worst-case value for a failed extraction."""
    return top(DIM)