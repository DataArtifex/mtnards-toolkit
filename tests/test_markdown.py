import os


import pytest


@pytest.mark.skip(reason="requires external server")
def test_md_hvdnet_anes1948(hvdnet_server, tests_dir):
    catalog = hvdnet_server.get_catalog_by_id("us-anes")
    data_product = catalog.get_data_product_by_id("anes1948")
    assert data_product
    md = data_product.get_markdown()
    with open(os.path.join(tests_dir, "hvdnet_anes_1948.md"), "w") as f:
        f.write(md)
