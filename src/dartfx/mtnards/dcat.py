"""
DCAT support for MTNA RDS

"""

from collections.abc import Iterable
from typing import Any

from rdflib import Graph

from dartfx.dcat import dcat

from .catalog import MtnaRdsCatalog
from .data_product import MtnaRdsDataProduct
from .server import MtnaRdsServer


class MtnaRdsDcat:
    """
    DCAT exporter for MTNA RDS servers, catalogs, and data products.
    """

    server: MtnaRdsServer
    catalogs: set[MtnaRdsCatalog]
    datasets: set[MtnaRdsDataProduct]
    uri_style: str | None

    def __init__(
        self,
        server: MtnaRdsServer,
        datasets: set[MtnaRdsDataProduct | str] | None = None,
        catalog: MtnaRdsCatalog | None = None,
        data_product: MtnaRdsDataProduct | None = None,
        uri_style: str | None = None,
    ):
        """
        Initializes the DCAT exporter.

        Args:
            server: The MTNA RDS server to export from.
            datasets: A set of data products to include.
            catalog: Optional single catalog to include.
            data_product: Optional single data product to include.
            uri_style: Optional URI generation style (currently unused by this exporter).
        """
        self.server = server
        self.uri_style = uri_style
        self.catalogs = set()
        self.datasets = set()
        if datasets:
            self.add_datasets(datasets)
        if catalog:
            self.add_catalog(catalog)
        if data_product:
            self.add_dataset(data_product)

    def graph(self) -> Graph:
        """Alias for :meth:`get_graph` for backward compatibility with documentation."""
        return self.get_graph()

    def get_prefixes_ttl(self, dataset: MtnaRdsDataProduct) -> str:
        prefixes = f"@prefix catalog: <{dataset._catalog._server.host}/>."
        prefixes += """
        @prefix hvdn: <https://rdf.highvaluedata.net/dcat#> .

        @prefix dcat: <http://www.w3.org/ns/dcat#> .
        @prefix dcterms: <http://purl.org/dc/terms/> .
        @prefix foaf: <http://xmlns.com/foaf/0.1/> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        """
        return prefixes

    def add_catalog(self, catalog: MtnaRdsCatalog | str) -> None:
        """Adds a single catalog to the generator"""
        self.add_catalogs([catalog])

    def add_catalogs(self, catalogs: Iterable[MtnaRdsCatalog | str]) -> None:
        """Adds catalogs to the generator"""
        for item in catalogs:
            if isinstance(item, MtnaRdsCatalog):
                self.catalogs.add(item)
            elif isinstance(item, str):
                raise NotImplementedError
            else:
                raise ValueError(f"Unexpected catalog type: {type(item)}")

    def add_dataset(self, dataset: MtnaRdsDataProduct | str) -> None:
        """Adds a single dataset to the generator"""
        self.add_datasets([dataset])

    def add_datasets(self, datasets: Iterable[MtnaRdsDataProduct | str]) -> None:
        """Adds datasets to the generator"""
        for item in datasets:
            if isinstance(item, MtnaRdsDataProduct):
                self.datasets.add(item)
            elif isinstance(item, str):
                raise NotImplementedError()
            else:
                raise ValueError(f"Unexpected dataset type: {type(item)}")

    def _create_dcat_catalog(self, rds_catalog: MtnaRdsCatalog, stub_only: bool = False) -> dcat.Catalog:
        """Internal helper to generates a DCAT graph for a catalog"""
        dcat_catalog = dcat.Catalog(id=rds_catalog.uri)
        dcat_catalog.add_title(rds_catalog.name or rds_catalog.id)
        if rds_catalog.description:
            dcat_catalog.add_description(rds_catalog.description)
        dcat_catalog.add_publisher(f"{rds_catalog._server.host}")
        if not stub_only and rds_catalog.data_products:
            for rds_data_product in rds_catalog.data_products:
                dcat_dataset = self._create_dcat_dataset(rds_data_product)
                dcat_catalog.add_dataset(dcat_dataset)
                dcat_api = self._create_dcat_api_service(rds_data_product, dcat_dataset)
                dcat_catalog.add_service(dcat_api)  # add service to catalog
        return dcat_catalog

    def _create_dcat_dataset(
        self,
        rds_data_product: MtnaRdsDataProduct,
    ) -> dcat.Dataset:
        dcat_dataset = dcat.Dataset(id=rds_data_product.uri)
        dcat_dataset.add_title(rds_data_product.name or rds_data_product.id)
        if rds_data_product.description:
            dcat_dataset.add_description(rds_data_product.description)
        explorer_url = f"{self.server.host}/explorer/explore/{rds_data_product._catalog.id}/{rds_data_product.id}"
        dcat_dataset.add_landing_page(explorer_url)
        if rds_data_product.last_update:
            dcat_dataset.add_modified_date(rds_data_product.last_update)
        dcat_dataset.add_publisher(f"{rds_data_product._catalog._server.host}")
        return dcat_dataset

    def _create_dcat_api_service(
        self,
        rds_data_product: MtnaRdsDataProduct,
        dcat_dataset: dcat.Dataset,
    ) -> dcat.DataService:
        dcat_api = dcat.DataService(id=f"{rds_data_product.uri}-api")
        dcat_api.add_served_dataset(dcat_dataset)
        dcat_api.add_conforms_to(rds_data_product._catalog._server.base_url + "/swagger")
        dcat_api.add_endpoint_url(rds_data_product._catalog._server.api_url)
        dcat_api.add_type("https://highvaluedata.net/vocab/service_type#MtnaRdsOpenAPI")
        return dcat_api

    def _add_resource_to_graph(self, resource: Any, graph: Graph) -> None:
        """Handle both supported graph export method names from dartfx-dcat resources."""
        if hasattr(resource, "add_to_rdf_graph"):
            resource.add_to_rdf_graph(graph)
            return
        if hasattr(resource, "add_to_graph"):
            resource.add_to_graph(graph)
            return
        msg = f"Unsupported DCAT resource type without graph export method: {type(resource)}"
        raise AttributeError(msg)

    def get_graph(self) -> Graph:
        """Generates RDF graph for server, catalogs, and datasets.
        The workflow is as follows:
        - Generate DCAT graph
        - Initialize the server catalog
        - Initialize the catalogs
        - Initialize the datasets add to graph
        - Add datasets to graph
        - Add server catalog to graph

        """
        g = Graph()

        #
        # Server Catalog
        #
        dcat_server_catalog = dcat.Catalog(id=f"{self.server.host}")
        dcat_server_catalog.add_publisher(f"{self.server.host}")

        # Loop over catalogs
        dcat_catalogs: dict[str, dcat.Catalog] = {}  # keeps track of catalogs being added
        for rds_catalog in self.catalogs:
            catalog_resource = self._create_dcat_catalog(rds_catalog)
            dcat_server_catalog.add_catalog(catalog_resource)  # add to server level catalog
            dcat_catalogs[rds_catalog.uri] = catalog_resource  # register

        # Loop over datasets
        for rds_data_product in self.datasets:
            # add data product's catalog if needed
            rds_catalog = rds_data_product._catalog
            dataset_catalog_resource = dcat_catalogs.get(rds_catalog.uri)
            if dataset_catalog_resource is None:
                dataset_catalog_resource = self._create_dcat_catalog(rds_catalog, stub_only=True)
                dcat_server_catalog.add_catalog(dataset_catalog_resource)  # add to server level catalog
                dcat_catalogs[rds_catalog.uri] = dataset_catalog_resource  # register

            # create DCAT dataset
            dcat_dataset = self._create_dcat_dataset(rds_data_product)
            dataset_catalog_resource.add_dataset(dcat_dataset)  # add dataset to catalog

            # create DCAT API service
            dcat_api = self._create_dcat_api_service(rds_data_product, dcat_dataset)
            dataset_catalog_resource.add_service(dcat_api)  # add service to catalog

            # add dataset resources to graph
            self._add_resource_to_graph(dcat_dataset, g)

            # add API service to graph
            self._add_resource_to_graph(dcat_api, g)

        # add catalogs to graph
        for catalog_resource in dcat_catalogs.values():
            self._add_resource_to_graph(catalog_resource, g)

        # add server catalog to graph
        self._add_resource_to_graph(dcat_server_catalog, g)
        return g
