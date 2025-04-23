import logging
import os
import sys
from dartfx.mtnards import MtnaRdsServer, MtnaRdsCatalog, MtnaRdsDataProduct, MtnaRdsVariable
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)
logger.info("Starting MCP server...")
sys.stderr.flush()

# Load environment variables
load_dotenv()

# Create an MCP server

instructions = """
This server provides tools to search and retrieve datasets from the MTNA Rich Data Services (RDS) API.

Use the available tools to:
- retrieve a list of available catalogs and their data products
- retrieve metadata and documentation for datasets
- retrieve information about data products variables
- subset data products based on variable names and values
- tabulate/aggregate data products using variables as dimension and measures

Some core concepts and synonyms:
- Catalog: collection, library, repository
- Data Product: dataset, data file, database
- Variable: field, column
- Dimension: a categorical variable that can be used to as a table row or column when tabulation a data product
- Measure: a continuous variable that can be used in a table cell when tabulating a data product
"""

mcp = FastMCP("Rich Data Services MCP Server for High-Value Data Network")

rds_server = MtnaRdsServer(host=os.getenv("MTNA_RDS_HOST","rds.highvaluedata.net"), api_key=os.getenv("MTNA_RDS_API_KEY"))
logging.info(f"Connecting to MTNA RDS server at {rds_server.host}...")
logging.info(rds_server.info)
sys.stderr.flush()

# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

@mcp.resource("mtnards://catalog")
def get_server_catalogs() -> list:
    """Retrieves all the catalogs available on the server along with their underlying data products."""
    response = []
    catalogs = rds_server.catalogs  
    for catalog in catalogs.values():   
        catalog_info = {
            "uri": catalog.uri,
            "id": catalog.id,
            "name": catalog.name,
            "description": catalog.description,
            "data_products": []
        }
        for data_product in catalog.data_products:
            data_product_info = {
                "uri": data_product.uri,
                "id": data_product.id,
                "name": data_product.name,
                "description": data_product.description
            }
            catalog_info["data_products"].append(data_product_info)
        response.append(catalog_info)
    return response

#@mcp.resource("mtnards://catalog/{catalog_id}")
#def get_catalog(catalog_id) -> MtnaRdsCatalog:
#    """Retrieves a catalog by its ID"""
#    catalog = rds_server.get_catalog_by_id(catalog_id)
#   return catalog

#@mcp.resource("mtnards://catalog/{catalog_id}/metadata")
#def get_catalog_metadata(catalog_id) -> MtnaRdsCatalog:
#    """Retrieves all classifications and variables in a catalog."""
#    catalog = rds_server.get_catalog_by_id(catalog_id)
#    return catalog


#@mcp.resource("mtnards://catalog/{catalog_id}/{data_product_id}")
#def get_data_product(catalog_id, data_product_id) -> MtnaRdsDataProduct:
#    """Retrieves a catalog by its ID"""
#    catalog = rds_server.get_catalog_by_id(catalog_id)
#    data_product_id = catalog.get_data_product_by_id(data_product_id)
#   return catalog

#@mcp.resource("mtnards://catalog/{catalog_id}/{data_product_id}/variables") 
#def get_data_product_variables(catalog_id, data_product_id) -> list[MtnaRdsVariable]:
#    """Retrieves all variables in a data product."""
#    catalog = rds_server.get_catalog_by_id(catalog_id)
#    data_product = catalog.get_data_product_by_id(data_product_id)
#    variables = data_product.get_variables()
#    if variables is None:
#        raise mcp.McpError("No variables found in the data product.")
#    return data_product.variables.values


if __name__ == "__main__":
    try:
        mcp.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)