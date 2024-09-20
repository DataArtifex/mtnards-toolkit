import logging
import os
import requests
import time


class MtnaRdsResource():
    uri: str
    id: str
    name: str
    description: str

    def __init__(self) -> None:
        self.uri =None
        self.id = None
        self.name = None

class MtnaRdsServer(MtnaRdsResource):
    host: str
    base_path: str
    api_path: str
    api_key: str
    ssl_verify : bool
    _catalogs: dict[str,"MtnaRdsCatalog"]
    _info: dict

    def __init__(self, host=None, base_path="rds", api_path="api", api_key=None, ssl_verify=True) -> None:
        super().__init__()
        self.host = host
        self.base_path = base_path
        self.api_path = f"{self.base_path}/{api_path}" if base_path else api_path
        self.api_key = api_key
        self.ssl_verify = ssl_verify
        self._catalogs = None
        self._info = None

    @property
    def catalogs(self, refresh=False) -> dict[str,"MtnaRdsCatalog"]:
        if refresh or self._catalogs is None:
            if refresh:
                self._catalogs = None
            # get from server
            response = self.api_request("catalog")
            if response.status_code == 200:
                data = response.json()
                self._catalogs = dict()
                for item in data['catalogs']:
                    uri = item['uri']
                    catalog = MtnaRdsCatalog(self)
                    catalog.from_json(item)
                    self._catalogs[uri] = catalog
            else:
                logging.error(f"Could not get server level catalog: {response.status_code}")
        return self._catalogs
    
    @property
    def base_url(self):
        return f"{self.host}/{self.base_path}"

    @property
    def api_url(self):
        return f"{self.host}/{self.api_path}"
    
    @property
    def info(self):
        if self._info is None:
            response = self.api_request("server/info")
            if response.status_code == 200:
                self._info = response.json()
            else:
                logging.error(f"Could not get server info: {response.status_code}")
        return self._info

    """
    Helper to make HTTP request to ths server
    """
    def api_request(self, path, method="GET", headers=None, params:dict=None, body_json=None, body_data=None):
        if headers is None:
            headers = {}
        if "X-API-KEY" not in headers and self.api_key:
            headers["X-API-KEY"] = self.api_key
        url = f"{self.api_url}/{path}"
        response = requests.request(method, url, headers=headers, params=params, json=body_json, verify=self.ssl_verify)
        return response

    def create_catalog(self, id, name=None, description=None, is_private=True, lang="en", timeout=10):
        body = {
            "id": id,
            "name": [
                {
                    "facetId": lang,
                    "value": name
                }
            ],
            "description": [
                {
                    "facetId": lang,
                    "value": description
                }
            ],
            "isPrivate": is_private
        }
        response = self.api_request("management/catalog", method="POST", body_json=body)
        if response.status_code == 200:
            process_id = response.json()
            return process_id
        else:
            logging.error(f"Could not create catalog: {response.status_code}")
    
    def delete_catalog(self, uri):
        response = self.api_request(f"management/catalog/{uri}", method="DELETE")
        if response.status_code == 200:
            process_id = response.json()
            return process_id
        else:
            logging.error(f"Could not delete catalog: {response.status_code}")

    def delete_data_product(self, catalog_uri, data_product_uri):
        path = f"management/catalog/{catalog_uri}/product/{data_product_uri}"
        result = self.api_request(path, method="DELETE")
        if result.status_code == 200:
            return result.json()
        else:
            logging.error(f"Could not delete data product: {result.status_code}")

    def get_catalog_by_uri(self, uri):
        return self.catalogs[uri]

    def get_catalog_by_id(self, uri):
        for catalog in self.catalogs.values():
            if catalog.id == uri:
                return catalog

    def get_import_configuration(self, catalog_uri, product_uri, file_info):
        path = f"management/catalog/{catalog_uri}/product/{product_uri}/import/configure"
        response = self.api_request(path, method="POST", body_json=file_info)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            logging.error(f"Could not get import configuration: {response.status_code}")

    def get_info(self):
        path = "server/info"
        response = self.api_request(path)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Could not get server info: {response.status_code}")

    def get_postman_collection(self, catalog_id=None, data_product_id=None):
        """Returns a Postman collection for the server, a catalog, or a data product.
        """
        url = "management/postman"
        if catalog_id:
            url += f"/{catalog_id}"
            if data_product_id:
                url += f"/{data_product_id}"
        params = {
            "rdsBaseUrl": self.base_url,
            "rdsExplorerBaseUrl": f"{self.base_url}/explorer/explore",
            "rdsTabEngineBaseUrl": f"{self.base_url}/tabengine/tabulation",
        }
        logging.debug(url)
        result = self.api_request(url, method="GET", params=params)
        if result.status_code == 200:
            data = result.json()
            # patch
            del data['info']['_postman_id'] # remove to prevent an invalidUidError
            return data
        else:
            logging.error(f"Could not retrieve Postman collection: {result.status_code}")

    def get_process_details(self, process_id) -> "MtnaRdsProcess":
        path = f"management/catalog/process/details/{process_id}"
        response = self.api_request(path)
        if response.status_code == 200:
            process = MtnaRdsProcess(self)
            process.from_json(response.json())
            return process
        else:
            logging.error(f"Could not get process details: {response.status_code}")

    def import_file(self, catalog_uri, product_uri, import_confifguration):
        path = f"management/catalog/{catalog_uri}/product/{product_uri}/import"
        response = self.api_request(path, method="POST", body_json=import_confifguration)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Could not import: {response.status_code}")

    def is_up(self):
        return self.get_info() is not None

    def upload_file(self, filepath):
        url = f"{self.base_url}/_files/upload"
        if os.path.isfile(filepath):
            with open(filepath, 'rb') as f:
                files = {'file': f}
                response = requests.post(url, files=files, headers={"X-API-KEY": self.api_key}, verify=self.ssl_verify)
                if response.status_code == 200:
                    return response.json()
                else:
                    logging.error(f"Could not upload file: {response.status_code}")

    def wait_for_process(self, pid, sleep=1, timeout=60*5, max_get_errors=10) -> "MtnaRdsProcess":
        start = time.time()
        get_errors = 0
        process_details = None
        while time.time() - start < timeout:
            process_details = self.get_process_details(pid)
            if process_details:
                logging.debug(f"Process {pid} status {process_details.status} ({process_details.completed}%)")
                if process_details.completed == 100:
                    break
            else:
                logging.debug("Failed to retrieve process {pid} details ({get_errors}/{max_get_errors})")
                get_errors += 1
                if get_errors > max_get_errors:
                    logging.error(f"Retrieving process {pid} details failed too many times ({get_errors})")
                    break
            time.sleep(sleep)
        # return last status
        return process_details

"""
Wrapper class for a catalog
"""
class MtnaRdsCatalog(MtnaRdsResource):
    _server: "MtnaRdsServer"
    _last_update: str
    _is_private: bool
    _data_products: dict[str, "MtnaRdsDataProduct"]

    def __init__(self, server: "MtnaRdsServer", uri=None) -> None:
        super().__init__()
        self._server = server
        self.uri = uri   
        self._data_products = None
        self._is_private = None

    @property
    def data_products(self):
        return self._data_products
    
    @property 
    def server(self):
        return self._server

    def __str__(self):
        text = ""
        if self._server:
            text += f"server uri: {self._server.uri}\n"
        for attribute, value in vars(self).items():
            if attribute in ["_server", "_data_products"]:
                continue
            text += f"{attribute}: {value}\n"
        if self._data_products:
            text += f"#data_products: {len(self._data_products)}\n"
        return text

    def get_import_configuration(self, product_uri, file_info):
        return self.server.get_import_configuration(self.uri, product_uri, file_info)

    def get_data_product_by_uri(self, uri):
        return self._data_products[uri]
    
    def get_data_product_by_id(self, uri):
        for product in self._data_products.values():
            if product.id == uri:
                return product
    
    def from_json(self, data) -> None:
        self.uri = data['uri']
        self.id = data['id']
        self.name = data.get('name')
        self._last_update = data.get('lastUpdate')
        self._is_private = data.get('isPrivate')
        self._data_products = dict()
        if 'dataProducts' in data:
            for item in data['dataProducts']:
                uri = item['uri']
                data_product = MtnaRdsDataProduct(self)
                data_product.from_json(item)
                self._data_products[uri] = data_product

    def create_sql_data_product(self, id, connection_string: str, table_name:str, username:str, password:str, name:str=None, description:str=None, is_private=True, lang="en"):
        if not name:
            name = id
        body = {
            "dataSource": {
                "id": id,
                "configuration": {
                    "$type": "SQL",
                    "tableName": table_name,
                    "connectionString": connection_string,
                    "user": username,
                    "password": password
                }
            },
            "description": [
                {
                    "facetId": lang,
                    "value": description
                }
            ],
            "id": id,
            "isPrivate": is_private,
            "name": [
                {
                    "facetId": lang,
                    "value": name
                }
            ]
        }
        url = f"management/catalog/{self.uri}/product"
        result = self.server.api_request(url, method="POST", body_json=body)
        if result.status_code == 200:
            return result.json()
        else:
            logging.error(f"Could not create data product: {result.status_code}")
    
    def delete(self):
        return self.server.delete_catalog(self.uri)

    def delete_data_product(self, data_product_uri):
        return self.server.delete_data_product(self.uri, data_product_uri)

    def get_postman_collection(self, data_product_id=None):
        """Returns a Postman collection for this catalog or one of its data product."""
        return self.server.get_postman_collection(self.id, data_product_id)

"""
Wrapper class for a data product
"""        
class MtnaRdsDataProduct(MtnaRdsResource):
    _catalog: "MtnaRdsCatalog"
    _cached: bool
    _changeLog: list
    _data_product_type: str
    _is_private: bool
    _last_update: str
    _reference: bool
    _revision_number: int

    def __init__(self, catalog: "MtnaRdsCatalog", uri=None) -> None:
        super().__init__()
        self._catalog = catalog
        self.uri = uri
        self._cached = None
        self._changeLog = None
        self._dataProductType = None
        self._is_private = None
        self._last_update = None
        self._reference = None
        self._revision_number = None

    @property
    def catalog(self):
        return self._catalog

    def from_json(self, data) -> None:
        self.uri = data['uri']
        self.id = data['id']
        self.name = data.get('name')
        self.description = data.get('description')
        self._cached = data.get('cached')
        self._changeLog = data.get('changeLog')
        self._data_product_type = data.get('dataProductType')
        self._is_private = data.get('isPrivate')
        self._last_update = data.get('lastUpdate')
        self._reference = data.get('reference')
        self._revision_number = data.get('revisionNumber')

    def delete(self):
        return self.catalog.delete_data_product(self.uri)

    def get_import_configuration(self, file_info):
        return self.catalog.get_import_configuration(self.uri, file_info)
    
    def get_postman_collection(self):
        return self.catalog.server.get_postman_collection(self.catalog.id, self.id)
    
class MtnaRdsProcess():
    completed: int
    id: str
    failure: str
    method_id: str
    method_name: str
    resource_name: str
    resource_uri: str
    status: str
    completion_details: any

    def __init__(self, server: "MtnaRdsServer", data=None) -> None:
        self.server = server
        self.completed = None
        self.id  = None
        self.failure  = None
        self.method_id = None
        self.method_name = None
        self.resource_name  = None
        self.resource_uri = None
        self.status = None
        self.completion_details = None
        if(data):
            self.from_json(data)

    @property
    def completed_successfully(self):
        return self.completed == 100 and self.status == "COMPLETED"

    @property
    def failed(self):
        return self.completed == 100 and self.status != "COMPLETED"
    
    @property
    def inprogress(self):
        return self.status != "PROCESSING"

    def from_json(self, data):
        self.completed = data.get('completed')
        self.id = data.get('id')
        self.method_id = data.get('methodId')
        self.method_name = data.get('methodName')
        self.resource_name = data.get('resourceName')
        self.resource_uri = data.get('resourceUri')
        self.status = data.get('status')
        self.completion_details = data.get('completionDetails')

    def __str__(self):
        text = ""
        for attribute, value in vars(self).items():
            if attribute == "server":
                continue
            text += f"{attribute}: {value}\n"
        return text

# NOT USED / FOR FUTURE DEVELOPMENT
class MtnaRdsProcessManager():
    _active_processes: dict[str,"MtnaRdsManagedProcess"]
    _completed_processes: dict[str,"MtnaRdsManagedProcess"]
    _failed_processes: dict[str,"MtnaRdsManagedProcess"]

    def __init__(self, server: "MtnaRdsServer") -> None:
        self.server = server
        self._active_processes = dict()
        self._completed_processes = dict()
        self._failed_processes = dict()

    @property
    def processes(self) -> dict[str,"MtnaRdsManagedProcess"]:
        return self
    
    @property
    def active_processes(self) -> dict[str,"MtnaRdsManagedProcess"]:
        return self._active_processes

    @property
    def completed_processes(self) -> dict[str,"MtnaRdsManagedProcess"]:
        return self._completed_processes

    @property
    def failed_processes(self) -> dict[str,"MtnaRdsManagedProcess"]:
        return self._failed_processes

    def refresh_active_process(self, id):
        pass

# NOT USED / FOR FUTURE DEVELOPMENT
class MtnaRdsManagedProcess():
    _context: any
    _process: MtnaRdsProcess

    def __init__(self, id, context: any) -> None:
        self._process = None
        self._context = context
