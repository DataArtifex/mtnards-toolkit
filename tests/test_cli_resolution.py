from unittest.mock import MagicMock

import pytest

from dartfx.mtnards.cli import RdsShell


@pytest.fixture
def mock_shell():
    shell = RdsShell(host="http://test", api_key="test-key")
    shell._server = MagicMock()
    return shell


def test_resolve_root(mock_shell):
    """Test resolution of root path."""
    res = mock_shell.resolve_path(None)
    assert res.type == "root"
    assert res.catalog_id is None
    assert res.product_id is None


def test_resolve_catalog(mock_shell):
    """Test resolution of a catalog path."""
    mock_catalog = MagicMock()
    mock_catalog.id = "cat1"
    mock_shell._server.get_catalog_by_id.return_value = mock_catalog

    res = mock_shell.resolve_path("cat1")
    assert res.type == "catalog"
    assert res.catalog_id == "cat1"
    assert res.obj == mock_catalog


def test_resolve_product(mock_shell):
    """Test resolution of a product path."""
    mock_catalog = MagicMock()
    mock_catalog.id = "cat1"
    mock_product = MagicMock()
    mock_product.id = "prod1"

    mock_shell._server.get_catalog_by_id.return_value = mock_catalog
    mock_catalog.get_data_product_by_id.return_value = mock_product

    res = mock_shell.resolve_path("cat1.prod1")
    assert res.type == "product"
    assert res.catalog_id == "cat1"
    assert res.product_id == "prod1"
    assert res.obj == mock_product


def test_resolve_property(mock_shell):
    """Test resolution of a property using @."""
    mock_catalog = MagicMock()
    mock_catalog.id = "cat1"
    mock_catalog.name = "My Catalog"
    mock_shell._server.get_catalog_by_id.return_value = mock_catalog

    res = mock_shell.resolve_path("cat1@name")
    assert res.type == "property"
    assert res.catalog_id == "cat1"
    assert res.property_name == "name"
    assert getattr(res.obj, res.property_name) == "My Catalog"


def test_resolve_classification(mock_shell):
    """Test resolution of a classification using $."""
    mock_catalog = MagicMock()
    mock_catalog.id = "cat1"
    mock_product = MagicMock()
    mock_product.id = "prod1"
    mock_cls = MagicMock()
    mock_cls.id = "gender"

    mock_shell._server.get_catalog_by_id.return_value = mock_catalog
    mock_catalog.get_data_product_by_id.return_value = mock_product
    mock_product.get_classification_by_id.return_value = mock_cls

    res = mock_shell.resolve_path("cat1.prod1$gender")
    assert res.type == "classification"
    assert res.catalog_id == "cat1"
    assert res.product_id == "prod1"
    assert res.obj == mock_cls


def test_resolve_relative_up(mock_shell):
    """Test resolution of .. (up)."""
    mock_shell.catalog_id = "cat1"
    mock_shell.product_id = "prod1"

    # Need to mock the catalog retrieval for '..' resolution
    mock_catalog = MagicMock()
    mock_catalog.id = "cat1"
    mock_shell._server.get_catalog_by_id.return_value = mock_catalog

    res = mock_shell.resolve_path("..")
    assert res.type == "catalog"
    assert res.catalog_id == "cat1"
    assert res.product_id is None


def test_resolve_absolute_dot(mock_shell):
    """Test resolution starting with . (absolute from root)."""
    mock_shell.catalog_id = "current_cat"  # current focus

    mock_catalog = MagicMock()
    mock_catalog.id = "other_cat"
    mock_shell._server.get_catalog_by_id.return_value = mock_catalog

    # Path starting with . should be root-relative
    res = mock_shell.resolve_path(".other_cat")
    assert res.type == "catalog"
    assert res.catalog_id == "other_cat"
