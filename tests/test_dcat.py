from dartfx.mtnards.dcat import DcatGenerator


def test_dcat_hvdnet_anes1948(hvdnet_server):
    catalog = hvdnet_server.get_catalog_by_id("us_anes")
    data_product = catalog.get_data_product_by_id("anes1948")
    assert data_product
    generator = DcatGenerator(hvdnet_server, [data_product])
    g = generator.get_graph()
    assert g
    print(g.serialize(format="turtle"))


def test_dcat_mtna_anes1948(mtna_server):
    catalog = mtna_server.get_catalog_by_id("covid19")
    data_product = catalog.get_data_product_by_id("jhu_country")
    assert data_product
    generator = DcatGenerator(mtna_server, [data_product])
    g = generator.get_graph()
    assert g
    print(g.serialize(format="turtle"))
