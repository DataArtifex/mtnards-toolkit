from dartfx.mtnards import MtnaRdsServer
from dartfx.mtnards.dcat import DcatGenerator
import pytest

hvdnet_server = MtnaRdsServer("https://rds.highvaluedata.net")
mtna_server = MtnaRdsServer("https://public.richdataservice.com")

def test_dcat_anes1948():
    catalog = hvdnet_server.get_catalog_by_id("us_anes")
    data_product = catalog.get_data_product_by_id("anes1948")
    assert data_product
    generator = DcatGenerator(mtna_server, [data_product])
    g = generator.get_graph()
    assert g
    print(g.serialize(format='turtle'))
