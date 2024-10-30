"""
DCAT support for MTNA RDS

"""
from .mtnards import MtnaRdsServer, MtnaRdsDataProduct
from dartfx.rdf import utils as rdfutils
from dartfx.dcat import dcat
from rdflib import Graph, URIRef

class DcatGenerator:
    server: MtnaRdsServer
    datasets: set[MtnaRdsDataProduct]
    uri_generator: rdfutils.UriGenerator
    
    def __init__(self, server: MtnaRdsServer, datasets: set[MtnaRdsDataProduct|str] = None, uri_generator: rdfutils.UriGenerator = rdfutils.UuidUrnGenerator()):
        self.server = server
        self.datasets = set()
        if datasets: 
            self.add_datasets(datasets)

    def get_prefixes_ttl(self, dataset: MtnaRdsDataProduct) -> str:
        prefixes  = f"@prefix catalog: <{dataset.catalog.server.host}/>."
        prefixes += """
        @prefix hvdn: <https://rdf.highvaluedata.net/dcat#> .

        @prefix dcat: <http://www.w3.org/ns/dcat#> .
        @prefix dcterms: <http://purl.org/dc/terms/> .
        @prefix foaf: <http://xmlns.com/foaf/0.1/> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        """
        return prefixes
    
    def add_dataset(self, dataset: MtnaRdsDataProduct|str) -> None:
        self.add_datasets([dataset])

    def add_datasets(self, datasets: list[MtnaRdsDataProduct|str]) -> None:
        for item in datasets:
            if isinstance(item, MtnaRdsDataProduct):
                self.datasets.add(item)
            elif isinstance(item, str):
                self.datasets.add(MtnaRdsDataProduct(self.server, item))
            else:
                raise ValueError(f"Unexpected dataset type: {type(item)}")

    def get_graph(self) -> Graph:
        g = Graph()
        
        #
        # Initialize Server Catalog
        #
        dcat_server_catalog = dcat.Catalog()
        dcat_server_catalog.set_uri(f"{self.server.host}")
        #dcat_catalog.add_title(self.s
        # erver.name)
        dcat_server_catalog.add_publisher(f"{self.server.host}")
        #for value in self.server.publisher:
        #    dcat_catalog.add_publisher(value)
        #for value in self.server.spatial:
        #    dcat_catalog.add_spatial(value)
        
        
        # Loop over datasets
        dcat_catalogs = {}
        for rds_data_product in self.datasets:
            # add data product's catalog if needed
            rds_catalog = rds_data_product.catalog
            dcat_catalog = dcat_catalogs.get(rds_catalog.uri)
            if dcat_catalog is None:
                dcat_catalog = dcat.Catalog()
                dcat_catalog.set_uri(rds_catalog.uri)
                dcat_catalog.add_title(rds_catalog.name)
                if rds_catalog.description:
                    dcat_catalog.add_description(rds_catalog.description)
                dcat_catalog.add_publisher(f"{rds_data_product.catalog.server.host}")
                # add to server level catalog
                dcat_server_catalog.add_catalog(dcat_catalog)
                # add to graph
                dcat_server_catalog.add_catalog(dcat_catalog)
                # register
                dcat_catalogs[rds_catalog.uri] = dcat_catalog
            
            #
            # populate DCAT dataset
            #
            dcat_ds = dcat.Dataset()
            dcat_ds.set_uri(rds_data_product.uri)
            dcat_ds.add_title(rds_data_product.name)

            if rds_data_product.description:
                dcat_ds.add_description(rds_data_product.description)

            #for keyword in rds_data_product.tags:
            #    dcat_ds.add_keyword(keyword)
                
            explorer_url = f"{self.server.host}/explorer/explore/{rds_data_product.catalog.id}/{rds_data_product.id}"
            dcat_ds.add_landing_page(explorer_url)
            
            #if rds_data_product.license_id:
            #    dcat_ds.add_license(rds_data_product.license_id)
            #if rds_data_product.license_name:
            #    dcat_ds.add_license(rds_data_product.license_name)
            #if rds_data_product.license_link:
            #    dcat_ds.add_license(rds_data_product.license_link)
            dcat_ds.add_modified_date(rds_data_product._last_update)
            
            dcat_ds.add_publisher(f"{rds_data_product.catalog.server.host}")

            #for value in rds_data_product.server.spatial:
            #    dcat_ds.add_spatial(value)

            # add dataset to catalog
            dcat_catalog.add_dataset(dcat_ds)

            #
            # populate DCAT CSV distribution
            #
            #dcat_csv = dcat.Distribution()
            #dcat_csv.set_uri(rds_data_product.csv_download_url)
            #dcat_csv.add_download_url(rds_data_product.csv_download_url)
            #dcat_csv.add_media_type("http://www.iana.org/assignments/media-types/text/csv")
            # add distribution to graph
            #dcat_csv.add_to_rdf_graph(g)
            # add distribution dataset
            #dcat_ds.add_distribution(dcat_csv)

            #
            # populate DCAT API service
            #
            dcat_api = dcat.DataService()
            dcat_api.set_uri(f"{rds_data_product.uri}-api")
            dcat_api.add_served_dataset(dcat_ds)
            dcat_api.add_conforms_to(rds_data_product.catalog.server.base_url+'/swagger')
            dcat_api.add_endpoint_url(rds_data_product.catalog.server.api_url)
            dcat_api.add_type("https://highvaluedata.net/vocab/service_type#MtnaRsdOpenDataAPI")
            # add service to catalog
            dcat_catalog.add_service(dcat_api)
            
            # add dataset resources to graph
            dcat_ds.add_to_rdf_graph(g)
            #dcat_csv.add_to_rdf_graph(g)
            dcat_api.add_to_rdf_graph(g)
        
        # add catalog to graph
        dcat_server_catalog.add_to_rdf_graph(g)
        return g
    