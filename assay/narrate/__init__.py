"""Optional LLM narration — prose only, and never a number the math didn't produce.

The report renders fully without this package. When enabled, an LLM (behind the provider-agnostic
:mod:`assay.narrate.llm`) writes the plain-English prose around the numbers, and
:func:`assay.narrate.narrate.assert_grounded` rejects any prose that introduces a new number.
"""

from .narrate import assert_grounded, plain_summary

__all__ = ["assert_grounded", "plain_summary"]
