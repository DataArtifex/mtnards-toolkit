from collections.abc import Callable
from typing import Any, TypeVar, cast

import pytest

from dartfx.mtnards import MtnaRdsServer
from dartfx.mtnards.dcat import MtnaRdsDcat

TestFunc = TypeVar("TestFunc", bound=Callable[..., Any])
skip_external = cast(Callable[[TestFunc], TestFunc], pytest.mark.skip(reason="requires external server"))


@skip_external
def test_dcat_hvdnet_anes1948(hvdnet_server: MtnaRdsServer) -> None:
    catalog = hvdnet_server.get_catalog_by_id("us-anes")
    assert catalog
    data_product = catalog.get_data_product_by_id("anes1948")
    assert data_product
    generator = MtnaRdsDcat(hvdnet_server, {data_product})
    g = generator.get_graph()
    assert g
    print(g.serialize(format="turtle"))


@skip_external
def test_dcat_mtna_anes1948(mtna_server: MtnaRdsServer) -> None:
    catalog = mtna_server.get_catalog_by_id("covid19")
    assert catalog
    data_product = catalog.get_data_product_by_id("jhu_country")
    assert data_product
    generator = MtnaRdsDcat(mtna_server, {data_product})
    g = generator.get_graph()
    assert g
    print(g.serialize(format="turtle"))
