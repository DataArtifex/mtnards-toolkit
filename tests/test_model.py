import json
import logging
import sys

import pytest

from dartfx.mtnards import MtnaRdsCatalog, MtnaRdsServer, MtnaRdsVariable

# Set up logging
logging.basicConfig(  # noqa: F821
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", stream=sys.stderr
)
logger = logging.getLogger(__name__)
sys.stderr.flush()


#
# SERVER
#
def test_hvdnet_server(hvdnet_server):
    assert hvdnet_server
    assert hvdnet_server.base_path == "rds"
    assert hvdnet_server.api_path == "api"
    assert hvdnet_server.api_endpoint == "rds/api"
    print(hvdnet_server)


@pytest.mark.skip(reason="requires external server")
def test_hvdnet_server_info(hvdnet_server):
    assert hvdnet_server.info
    print(hvdnet_server.info)
    assert hvdnet_server.info.name
    assert hvdnet_server.info.released
    assert hvdnet_server.info.version


#
# CATALOGS
#
@pytest.mark.skip(reason="requires external server")
@pytest.mark.dependency(name="test_server_info")
def test_hvdnet_catalogs(hvdnet_server):
    assert hvdnet_server.catalogs
    assert len(hvdnet_server.catalogs) > 1
    print(hvdnet_server.catalogs.keys())
    print(hvdnet_server.catalogs["us-anes"]._server)


def test_dummy_anes_catalog():
    dummy_server = MtnaRdsServer(host="https://example.org")
    data = US_ANES_CATALOG
    catalog = MtnaRdsCatalog(_server=dummy_server, **data)
    assert catalog
    assert len(catalog.data_products) == 1
    print(catalog)


#
# CATALOG
#
@pytest.mark.skip(reason="requires external server")
@pytest.mark.dependency(name="test_hvdnet_catalogs")
def test_hvdnet_anes_catalog(hvdnet_server):
    catalog = hvdnet_server.get_catalog_by_id("us-anes")
    assert catalog
    assert len(catalog.data_products) == 1
    print(catalog)


#
# DATA PRODUCT
#


@pytest.mark.skip(reason="requires external server")
def test_hvdnet_anes1948_metadata(hvdnet_server):
    catalog = hvdnet_server.get_catalog_by_id("us-anes")
    data_product = catalog.get_data_product_by_id("anes1948")
    assert data_product
    data_product.load_metadata()
    assert data_product._variables
    assert data_product._classifications
    for variable in data_product._variables.values():
        assert isinstance(variable, MtnaRdsVariable)
    for classification in data_product._classifications.values():
        assert classification._codes


#
# VARIABLES
#


def test_dummy_variable():
    variable = MtnaRdsVariable(**US_ANES_V4800003)
    assert variable
    print(variable)


@pytest.mark.skip(reason="requires external server")
def test_hvdnet_anes1948_variables(hvdnet_server):
    catalog = hvdnet_server.get_catalog_by_id("us-anes")
    product = catalog.get_data_product_by_id("anes1948")
    assert product
    assert product.variables
    assert len(product.variables) > 0
    print(len(product.variables))


@pytest.mark.skip(reason="requires external server")
def test_hvdnet_anes1948_v480003(hvdnet_server):
    catalog = hvdnet_server.get_catalog_by_id("us-anes")
    product = catalog.get_data_product_by_id("anes1948")
    variable = product.get_variable_by_id("V480003")
    assert variable
    print(type(variable))
    print(variable)

    variable = variable.resolve()
    assert variable
    print(type(variable))
    print(variable)


#
# CLASSIFICATIONS
#
@pytest.mark.skip(reason="requires external server")
def test_hvdnet_anes1948_classifications(hvdnet_server):
    catalog = hvdnet_server.get_catalog_by_id("us-anes")
    product = catalog.get_data_product_by_id("anes1948")
    assert product
    assert product.classifications
    assert len(product.classifications) > 0
    print(len(product.classifications))


@pytest.mark.skip(reason="requires external server")
def test_hvdnet_anes1948_classification_V480003(hvdnet_server):
    catalog = hvdnet_server.get_catalog_by_id("us-anes")
    product = catalog.get_data_product_by_id("anes1948")
    classification = product.get_classification_by_id("V480003")
    assert classification
    print(type(classification))
    print(classification.codes)
    assert classification.code_count == 3
    classification = classification.resolve()
    print(type(classification))
    print(classification.codes)
    assert classification.code_count == 3


#
# TEST RESOURCES
#
# Long description truncated for line length
_ANES_DESC = (
    "This study is part of a time-series collection of national surveys "
    "fielded continuously since 1952. The election studies are designed to "
    "present data on Americans' social backgrounds, enduring political "
    "predispositions, social and political values, perceptions and "
    "evaluations of groups and candidates, opinions on questions of public "
    "policy, and participation in political life."
)

US_ANES_CATALOG = json.loads(
    """{
    "dataProducts": [
        {
            "abbreviation": "American National Election Study, 1948",
            "cached": true,
            "changeLog": [],
            "dataProductType": "DATA_PRODUCT",
            "description": """
    + json.dumps(_ANES_DESC)
    + """,
            "id": "anes1948",
            "isPrivate": false,
            "lastUpdate": "2024-03-28T20:55:00.287Z",
            "name": "ANES 1948 Time Series Study",
            "reference": false,
            "revisionNumber": 3,
            "uri": "c0779d53-6926-43d7-a832-7a74b0a0978f"
        }
    ],
    "id": "us-anes",
    "isPrivate": false,
    "lastUpdate": "2024-04-25T20:11:41.333Z",
    "name": "American National Election Studies",
    "uri": "8e9ab068-1a94-4191-a811-809f05559445"
}"""
)

US_ANES_V4800003 = json.loads("""
{
        "classificationId": "V480003",
        "classificationUri": "89734f8f-c91f-43f4-afb8-5dc6df68b51a",
        "dataType": "NUMERIC",
        "id": "V480003",
        "isDimension": true,
        "isMeasure": true,
        "isRequired": false,
        "isWeight": false,
        "label": "POP CLASSIFICATION",
        "lastUpdate": "2024-03-28T20:54:00.19Z",
        "name": "V480003",
        "storageType": "BIGINT",
        "uri": "ce24fc6d-3f2b-4d8a-be18-696e439f67d9"
    }""")
