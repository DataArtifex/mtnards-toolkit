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

.. autoclass:: dartfx.mtnards.mtnards.MtnaRdsServerInfo
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

.. autoclass:: dartfx.mtnards.mtnards.MtnaRdsClassification
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: dartfx.mtnards.mtnards.MtnaRdsClassificationCode
   :members:
   :undoc-members:
   :show-inheritance:

Base Classes
------------

.. autoclass:: dartfx.mtnards.mtnards.MtnaRdsResource
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__, __hash__

Type Definitions
----------------

The module uses type hints extensively. Common types include:

* ``str | None`` - Optional string values
* ``dict[str, T]`` - Dictionary with string keys
* ``list[T]`` - List of objects of type T
* ``bool | None`` - Optional boolean values

All public APIs include complete type hints for parameters and return values.
