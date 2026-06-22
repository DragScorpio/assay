"""Valuation methods, each an isolated module with one shared contract (:mod:`assay.models.base`).

A method takes tier-tagged figures + explicit assumptions and returns a value range. Methods never
read each other's state; the engine just runs them all and triangulates. Adding a method is adding
one class.
"""

from .asset_value import AssetValueModel
from .base import Assumption, CompanyInputs, ModelResult, ValuationModel, ValueRange
from .dcf import DcfModel
from .earnings_power import EarningsPowerModel

#: The default panel the engine triangulates over. Order is display order (floor -> growth).
DEFAULT_MODELS: list[ValuationModel] = [
    AssetValueModel(),
    EarningsPowerModel(),
    DcfModel(),
]

__all__ = [
    "Assumption",
    "CompanyInputs",
    "ModelResult",
    "ValuationModel",
    "ValueRange",
    "DcfModel",
    "EarningsPowerModel",
    "AssetValueModel",
    "DEFAULT_MODELS",
]
