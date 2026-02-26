import json
import os

import pytest


@pytest.mark.skip(reason="requires external server")
def test_croissant_hvdnet_anes1948(hvdnet_server, tests_dir):
    catalog = hvdnet_server.get_catalog_by_id("us-anes")
    data_product = catalog.get_data_product_by_id("anes1948")
    assert data_product
    include_codes = True  # set to False when developing
    max_codes = 5  # 5 will produce a mix of data and examples for classification record sets
    croissant = data_product.get_croissant(include_codes=include_codes, max_codes=max_codes)
    assert croissant
    assert croissant.cite_as
    jsonld = croissant.to_json()
    with open(os.path.join(tests_dir, "hvdnet_anes_1948.croissant.jsonld"), "w") as f:
        json.dump(jsonld, f, indent=4, default=str)
