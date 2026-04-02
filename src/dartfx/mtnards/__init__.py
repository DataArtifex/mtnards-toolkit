# SPDX-FileCopyrightText: 2024-present kulnor <pascal.heus@gmail.com>
#
# SPDX-License-Identifier: MIT
from .base import MtnaRdsError  # noqa: F401
from .catalog import MtnaRdsCatalog  # noqa: F401
from .classification import MtnaRdsClassification, MtnaRdsClassificationCode, MtnaRdsClassificationStub  # noqa: F401
from .data_product import MtnaRdsDataProduct  # noqa: F401
from .process import MtnaRdsProcess  # noqa: F401
from .server import MtnaRdsServer  # noqa: F401
from .variable import MtnaRdsVariable, MtnaRdsVariableStub  # noqa: F401

__all__ = [
    "MtnaRdsError",
    "MtnaRdsCatalog",
    "MtnaRdsClassification",
    "MtnaRdsClassificationCode",
    "MtnaRdsClassificationStub",
    "MtnaRdsDataProduct",
    "MtnaRdsProcess",
    "MtnaRdsServer",
    "MtnaRdsVariable",
    "MtnaRdsVariableStub",
]

# Rebuild models that use forward references (TYPE_CHECKING imports).
# Required so Pydantic resolves deferred annotations before Sphinx autodoc
# or other introspection tools inspect the models.
_types_namespace = {
    "MtnaRdsCatalog": MtnaRdsCatalog,
    "MtnaRdsClassification": MtnaRdsClassification,
    "MtnaRdsClassificationCode": MtnaRdsClassificationCode,
    "MtnaRdsClassificationStub": MtnaRdsClassificationStub,
    "MtnaRdsDataProduct": MtnaRdsDataProduct,
    "MtnaRdsProcess": MtnaRdsProcess,
    "MtnaRdsServer": MtnaRdsServer,
    "MtnaRdsVariable": MtnaRdsVariable,
    "MtnaRdsVariableStub": MtnaRdsVariableStub,
}
MtnaRdsCatalog.model_rebuild(_types_namespace=_types_namespace)
MtnaRdsDataProduct.model_rebuild(_types_namespace=_types_namespace)
MtnaRdsProcess.model_rebuild(_types_namespace=_types_namespace)
MtnaRdsServer.model_rebuild(_types_namespace=_types_namespace)
