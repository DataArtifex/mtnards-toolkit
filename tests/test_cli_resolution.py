from unittest.mock import MagicMock

import pytest

from dartfx.mtnards.base import MtnaRdsPatchConflictError
from dartfx.mtnards.cli import RdsShell


@pytest.fixture
def mock_shell():
    shell = RdsShell(host="http://test", api_key="test-key")
    shell._server = MagicMock()
    return shell


def test_shell_uses_mtnards_api_key_from_environment(monkeypatch):
    """RdsShell should read the renamed API key environment variable when api_key is omitted."""
    monkeypatch.setenv("MTNARDS_API_KEY", "env-key")

    shell = RdsShell(host="http://test", api_key=None)

    assert shell.api_key == "env-key"


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


def test_do_set_patches_variable_property(mock_shell):
    """set should patch a variable property when a variable path is resolved."""
    mock_shell.catalog_id = "cat1"
    mock_shell.product_id = "prod1"

    mock_catalog = MagicMock()
    mock_catalog.id = "cat1"
    mock_product = MagicMock()
    mock_product.id = "prod1"
    mock_variable = MagicMock()
    mock_variable.id = "var1"

    mock_shell._server.get_catalog_by_id.return_value = mock_catalog
    mock_catalog.get_data_product_by_id.return_value = mock_product
    mock_product.get_variable_by_id.return_value = mock_variable

    mock_shell.do_set("var1@label", "Updated Label")

    mock_variable.patch.assert_called_once_with({"label": "Updated Label"})


def test_do_set_patches_product_property(mock_shell):
    """set should patch a product property when a product path is resolved."""
    mock_catalog = MagicMock()
    mock_catalog.id = "cat1"
    mock_product = MagicMock()
    mock_product.id = "prod1"

    mock_shell._server.get_catalog_by_id.return_value = mock_catalog
    mock_catalog.get_data_product_by_id.return_value = mock_product

    mock_shell.do_set("cat1.prod1@label", "New Product Label")

    mock_product.patch.assert_called_once_with({"label": "New Product Label"})


def test_do_set_rejects_classification_property(mock_shell, capsys):
    """set should reject classification property updates because classifications are not patchable."""
    mock_catalog = MagicMock()
    mock_catalog.id = "cat1"
    mock_product = MagicMock()
    mock_product.id = "prod1"
    mock_cls = MagicMock()
    mock_cls.id = "gender"

    mock_shell._server.get_catalog_by_id.return_value = mock_catalog
    mock_catalog.get_data_product_by_id.return_value = mock_product
    mock_product.get_classification_by_id.return_value = mock_cls

    mock_shell.do_set("cat1.prod1$gender@name", "New Name")
    out = capsys.readouterr().out

    assert "Classification properties are not patchable" in out
    mock_cls.patch.assert_not_called()


def test_do_set_reports_patch_conflict(mock_shell, capsys):
    """set should report patch conflicts clearly to the user."""
    mock_catalog = MagicMock()
    mock_catalog.id = "cat1"
    mock_shell._server.get_catalog_by_id.return_value = mock_catalog
    mock_catalog.patch.side_effect = MtnaRdsPatchConflictError("catalog", "cat1")

    mock_shell.do_set("cat1@name", "New Catalog Name")
    out = capsys.readouterr().out

    assert "Patch conflict" in out


def test_execute_line_set_allows_catalog_path_outside_product_context(mock_shell):
    """set should be available outside product context for catalog patching."""
    mock_shell.product_id = None
    mock_shell.do_set = MagicMock()

    should_continue = mock_shell.execute_line("set cat1@name 'New Catalog Name'")

    assert should_continue is True
    mock_shell.do_set.assert_called_once_with("cat1@name", "New Catalog Name", edit=False)


def test_execute_line_set_allows_data_product_path_outside_product_context(mock_shell):
    """set should be available outside product context for data product patching."""
    mock_shell.product_id = None
    mock_shell.do_set = MagicMock()

    should_continue = mock_shell.execute_line("set cat1.prod1@label 'New Product Label'")

    assert should_continue is True
    mock_shell.do_set.assert_called_once_with("cat1.prod1@label", "New Product Label", edit=False)


def test_execute_line_set_auto_quotes_unquoted_multi_word_value(mock_shell):
    """set should treat unquoted trailing tokens as a single value."""
    mock_shell.do_set = MagicMock()

    should_continue = mock_shell.execute_line("set @name American National Election Study")

    assert should_continue is True
    mock_shell.do_set.assert_called_once_with("@name", "American National Election Study", edit=False)


def test_execute_line_refresh_routes_to_do_refresh(mock_shell):
    """refresh should route through execute_line and pass optional path."""
    mock_shell.do_refresh = MagicMock()

    should_continue = mock_shell.execute_line("refresh cat1.prod1")

    assert should_continue is True
    mock_shell.do_refresh.assert_called_once_with("cat1.prod1")


def test_execute_line_show_json_routes_to_do_show(mock_shell):
    """show --json should enable JSON mode in do_show."""
    mock_shell.do_show = MagicMock()

    should_continue = mock_shell.execute_line("show cat1.prod1 --json")

    assert should_continue is True
    mock_shell.do_show.assert_called_once_with(
        path="cat1.prod1",
        limit=100,
        offset=0,
        codes_limit=0,
        as_json=True,
    )


def test_do_refresh_in_product_context_reloads_catalog_and_product_metadata(mock_shell):
    """refresh in product context should reload root catalogs, catalog details, and product metadata."""
    mock_shell.catalog_id = "cat1"
    mock_shell.product_id = "prod1"

    mock_catalog = MagicMock()
    mock_catalog.id = "cat1"
    mock_product = MagicMock()
    mock_product.id = "prod1"

    mock_shell._server.refresh_catalogs = MagicMock()
    mock_shell._server.get_catalog_by_id.return_value = mock_catalog
    mock_catalog.get_data_product_by_id.return_value = mock_product

    mock_shell.do_refresh()

    mock_shell._server.refresh_catalogs.assert_called_once_with()
    mock_shell._server.get_catalog_by_id.assert_any_call("cat1", fetch=True)
    mock_catalog.get_data_product_by_id.assert_any_call("prod1")
    mock_product.load_metadata.assert_called_once_with()


def test_variable_classification_ref_prefers_id(mock_shell):
    """classification_id should be used when present."""
    variable = MagicMock()
    variable.classification_id = "CLS1"
    variable.classification_uri = "classification-uri"

    assert mock_shell._variable_classification_ref(variable) == "CLS1"


def test_variable_classification_ref_falls_back_to_uri(mock_shell):
    """classification_uri should be shown when id is missing and cannot be resolved."""
    variable = MagicMock()
    variable.classification_id = None
    variable.classification_uri = "classification-uri"
    variable.classification = None

    assert mock_shell._variable_classification_ref(variable) == "classification-uri"


def test_json_data_for_current_resource_excludes_computed_fields(mock_shell):
    """show --json should serialize only the current resource fields."""
    model = MagicMock()
    model.model_dump.return_value = {"id": "var1", "name": "Variable 1"}

    payload = mock_shell._json_data_for_current_resource(model)

    assert payload == {"id": "var1", "name": "Variable 1"}
    model.model_dump.assert_called_once_with(by_alias=True, exclude_computed_fields=True)


def test_do_ls_root_includes_private_column(mock_shell, capsys):
    """Root ls output should show the isPrivate value for catalogs."""
    catalog = MagicMock()
    catalog.id = "cat1"
    catalog.name = "Catalog One"
    catalog.is_private = True
    mock_shell._server.catalogs = {"cat1": catalog}

    mock_shell.do_ls()
    out = capsys.readouterr().out

    assert "Private" in out
    assert "yes" in out


def test_do_ls_catalog_includes_private_column(mock_shell, capsys):
    """Catalog ls output should show the isPrivate value for products."""
    product = MagicMock()
    product.id = "prod1"
    product.name = "Product One"
    product.is_private = False

    catalog = MagicMock()
    catalog.id = "cat1"
    catalog.data_products = [product]

    mock_shell.resolve_path = MagicMock(return_value=MagicMock(type="catalog", catalog_id="cat1", obj=catalog))

    mock_shell.do_ls("cat1")
    out = capsys.readouterr().out

    assert "Private" in out
    assert "no" in out


def test_do_ls_product_summary_includes_private_value(mock_shell, capsys):
    """Product-context ls summary should show the product privacy state."""
    product = MagicMock()
    product.id = "prod1"
    product.name = "Product One"
    product.is_private = True
    product.variables = {}
    product.classifications = {}
    product.variables_count = 0

    mock_shell.resolve_path = MagicMock(
        return_value=MagicMock(
            type="product",
            classification_id=None,
            obj=product,
        )
    )

    mock_shell.do_ls("cat1.prod1")
    out = capsys.readouterr().out

    assert "Private:" in out
    assert "yes" in out
