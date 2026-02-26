Core API Reference
==================

This page documents the core classes and functions of the MTNA RDS Toolkit.

Server Connection
-----------------

.. autoclass:: dartfx.mtnards.MtnaRdsServer
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

.. autoclass:: dartfx.mtnards.base.MtnaRdsServerInfo
   :members:
   :undoc-members:
   :show-inheritance:

Catalog
-------

.. autoclass:: dartfx.mtnards.MtnaRdsCatalog
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Data Product
------------

.. autoclass:: dartfx.mtnards.MtnaRdsDataProduct
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Variable
--------

.. autoclass:: dartfx.mtnards.variable.MtnaRdsVariableStub
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

.. autoclass:: dartfx.mtnards.MtnaRdsVariable
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Classification
--------------

.. autoclass:: dartfx.mtnards.MtnaRdsClassificationStub
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

.. autoclass:: dartfx.mtnards.classification.MtnaRdsClassification
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: dartfx.mtnards.classification.MtnaRdsClassificationCode
   :members:
   :undoc-members:
   :show-inheritance:

Process
-------

.. autoclass:: dartfx.mtnards.process.MtnaRdsProcess
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Base Classes
------------

.. autoclass:: dartfx.mtnards.base.MtnaRdsResource
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__, __hash__, __eq__

Type Definitions
----------------

The module uses type hints extensively. Common types include:

* ``str | None`` - Optional string values
* ``dict[str, T]`` - Dictionary with string keys
* ``list[T]`` - List of objects of type T
* ``bool | None`` - Optional boolean values

All public APIs include complete type hints for parameters and return values.
