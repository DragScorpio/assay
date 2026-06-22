"""The report renders all layers, and the grounding guard has teeth.

The guard is Assay's trust mechanism: prose may only restate numbers the math produced. These tests
prove the deterministic summary passes and a fabricated number is caught.
"""

from assay.data.sample import acme_inputs
from assay.engine.report import build_report, render_markdown
from assay.engine.triangulate import triangulate
from assay.engine.valuability import assess
from assay.models import DEFAULT_MODELS
from assay.narrate import assert_grounded, plain_summary


def _report():
    inputs = acme_inputs()
    tri = triangulate(inputs, DEFAULT_MODELS)
    return build_report(inputs, tri, assess(inputs))


def test_report_renders_every_layer():
    md = render_markdown(_report())
    for marker in (
        "Layer 0",
        "Layer 1",
        "Layer 2",
        "Layer 3",
        "Layer 4",
        "Valuability",
        "Provenance ledger",
    ):
        assert marker in md


def test_plain_summary_is_grounded():
    report = _report()
    assert assert_grounded(plain_summary(report), report.allowed) == []


def test_guard_catches_a_fabricated_number():
    report = _report()
    fabricated = "The stock is secretly worth $999.99 per share."
    flagged = assert_grounded(fabricated, report.allowed)
    assert 999.99 in flagged
