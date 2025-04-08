import logging
from typing import Optional, Union
import mlcroissant as mlc
from markdownify import markdownify as md
import os
from pydantic import AliasChoices, BaseModel, Field, PrivateAttr, computed_field, model_validator, root_validator
import requests
import time

class MtnaRdsResource(BaseModel):
    uri: str
    id: str
    name: str | None = None
    description: str | None = None
    reference: bool | None = None
    revision_number: int | None = Field(alias="revisionNumber", default=None)

class MtnaRdsServerInfo(BaseModel):
    name: str
    released: str
    version: str

class MtnaRdsServer(BaseModel):
    host: str
    base_path: str = Field(default="rds")
    api_path: str = Field(default="api")
    api_key: str | None = None
    ssl_verify : bool = Field(default=True)
    _catalogs: dict[str,"MtnaRdsCatalog"] = None
    _info: MtnaRdsServerInfo | None = None

    @computed_field
    @property
    def api_endpoint(self) -> str:
        return f"{self.base_path}/{self.api_path}" if self.base_path else self.api_path

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
                    catalog = MtnaRdsCatalog(**item)
                    catalog._server = self
                    self._catalogs[catalog.id] = catalog
            else:
                logging.error(f"Could not get server level catalog: {response.status_code}")
        return self._catalogs
    
    @computed_field
    @property
    def base_url(self) -> str:
        return f"{self.host}/{self.base_path}"

    @computed_field
    @property
    def api_url(self) -> str:
        return f"{self.host}/{self.api_endpoint}"
    
    @property
    def info(self) -> MtnaRdsServerInfo:
        if self._info is None:
            response = self.api_request("server/info")
            if response.status_code == 200:
                data = response.json()
                self._info = MtnaRdsServerInfo(**data)
            else:
                logging.error(f"Could not get server info: {response.status_code}")
        return self._info


    @computed_field
    @property
    def explorer_url(self) -> str:
        return f"{self.host}/{self.base_path}/explorer"
    
    @computed_field
    @property
    def tabengine_url(self) -> str:
        return f"{self.host}/{self.base_path}/tabengine"

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
    
    def delete_catalog(self, id):
        response = self.api_request(f"management/catalog/{id}", method="DELETE")
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
        for catalog in self.catalogs.values():
            if catalog.uri == uri:
                return catalog

    def get_catalog_by_id(self, id):
        return self.catalogs.get(id)

    def get_ddi_codebook(self, catalog_id, product_id, include_variables=True, include_statistics=False):
        path = f"catalog/{catalog_id}/{product_id}/ddi-codebook?includeVariables={include_variables}&includeStatistics={include_statistics}"
        response = self.api_request(path)
        if response.status_code == 200:
            return response.content
        else:
            logging.error(f"Could not retrieve DDI-Codebook: {response.status_code} {path}")

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
            data = response.json()
            process = MtnaRdsProcess(server=self, **data)
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
    last_update: str = Field(alias="lastUpdate")
    is_private: bool = Field(alias="isPrivate")
    data_products: list["MtnaRdsDataProduct"] | None = Field(alias="dataProducts", default=None)

    _server: "MtnaRdsServer" = PrivateAttr(default=None) # This is set by the server @root_validator or programmatically

    @model_validator(mode="after")
    def attach_catalog_to_products(self):
        # attach the catalog to the data products
        if self.data_products:
            for product in self.data_products:
                product._catalog = self
        return self
    
    def __str__(self):
        text = ""
        if self._server:
            text += f"server uri: {self._server.host}\n"
        for attribute, value in vars(self).items():
            if attribute in ["server", "data_products"]:
                continue
            text += f"{attribute}: {value}\n"
        if self.data_products:
            text += f"#data_products: {len(self.data_products)}\n"
        return text

    def get_data_product_by_uri(self, uri):
        for product in self.data_products:
            if product.uri == uri:
                return product
    
    def get_data_product_by_id(self, id):
        for product in self.data_products:
            if product.id == id:
                return product

    def get_ddi_codebook(self, product_id, include_variables=True, include_statistics=True):
        return self._server.get_ddi_codebook(self.id, product_id, include_variables, include_statistics)

    def get_import_configuration(self, product_uri, file_info):
        return self._server.get_import_configuration(self.uri, product_uri, file_info)
   
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
        result = self._server.api_request(url, method="POST", body_json=body)
        if result.status_code == 200:
            return result.json()
        else:
            logging.error(f"Could not create data product: {result.status_code}")
    
    def delete(self):
        return self._server.delete_catalog(self.uri)

    def delete_data_product(self, data_product_uri):
        return self._server.delete_data_product(self.uri, data_product_uri)

    def get_postman_collection(self, data_product_id=None):
        """Returns a Postman collection for this catalog or one of its data product."""
        return self._server.get_postman_collection(self.id, data_product_id)

"""
Wrapper class for a data product
"""        
class MtnaRdsDataProduct(MtnaRdsResource):
    abbreviation: str | None  = None
    cached: bool | None = None
    doi: bool | None = None
    changeLog: list | None = None
    citation: str | None = None
    data_product_type: str | None = Field(alias="dataProductType", default=None)
    is_private: bool | None = Field(alias="isPrivate", default=None)
    keywords: list[str] | None = None
    last_update: str | None = Field(alias="lastUpdate", default=None)
    provenance: str | None = None
    urls: list[str] | None = None

    _catalog: MtnaRdsCatalog = PrivateAttr(default=None) # This is set by the catalog @root_validator or programmatically
    # variables and classifications are lazy loaded when the underlying property is accessed
    _variables: "Optional[list[MtnaRdsVariableStub | MtnaRdsVariable]]" = PrivateAttr(default=None) # key is variable id
    _classifications: "Optional[list[MtnaRdsClassificationStub | MtnaRdsClassification]]" = PrivateAttr(default=None) # key is classification id

    @computed_field
    @property
    def classifications(self) -> dict[str, Union["MtnaRdsClassificationStub","MtnaRdsClassification"]]:
        if self._classifications is None:
            # get from server
            response = self._catalog._server.api_request(f"catalog/{self._catalog.id}/{self.id}/classifications")
            if response.status_code == 200:
                data = response.json()
                self._classifications = dict()
                for item in data:
                    classification = MtnaRdsClassificationStub(**item)
                    classification._data_product = self
                    self._classifications[classification.id] = classification
            else:
                logging.error(f"Could not get variables: {response.status_code}")
        return self._classifications

    @computed_field
    @property
    def csv_download_url(self) -> str:
        return f"{self._catalog._server.api_url}/package{self._catalog.id}/{self.id}.csv"


    @computed_field
    @property
    def explorer_url(self) -> str:
        return f"{self._catalog._server.explorer_url}/explore/{self._catalog.id}/{self.id}"

    @computed_field
    @property
    def parquet_download_url(self) -> str:
        return f"{self._catalog._server.api_url}/package{self._catalog.id}/{self.id}.parquet"

    @computed_field
    @property
    def tabengine_url(self) -> str:
        return f"{self._catalog._server.tabengine_url}/tabulate/{self._catalog.id}/{self.id}"


    @computed_field
    @property
    def variables(self) -> dict[str,Union["MtnaRdsVariableStub","MtnaRdsVariable"]]:
        if self._variables is None:
            # get from server
            response = self._catalog._server.api_request(f"catalog/{self._catalog.id}/{self.id}/variables")
            if response.status_code == 200:
                data = response.json()
                self._variables = dict()
                for item in data:
                    variable = MtnaRdsVariableStub(**item)
                    variable._data_product = self
                    self._variables[variable.id] = variable
            else:
                logging.error(f"Could not get classifications: {response.status_code}")
        return self._variables

    def delete(self):
        return self._catalog.delete_data_product(self.uri)

    def get_classification_by_uri(self, uri):
        for classification in self.classifications:
            if classification.uri == uri:
                return classification
    
    def get_classification_by_id(self, id):
        return self.classifications.get(id)

    def get_croissant(self, include_codes=True, max_codes=100) -> mlc.Metadata:
        context = mlc.Context()
        context.is_live_dataset = True
        # metadata
        publishers = []
#        for publisher in self.server.publisher:
#            publishers.append(mlc.Organization(name=publisher, url=self.server.host))
        metadata = mlc.Metadata(ctx=context, 
            id=self.id,
            name=self.name,
            description=md(self.description),
            cite_as = self.citation,
            date_modified = self.last_update,
#            date_published = self.publication_date,
#            license = self.license,
            keywords=self.keywords,
            publisher=publishers,
            url=self.explorer_url,
            version = int(self.revision_number)
        )
        # distribution
        distribution = []
        # csv distribution
        content_url = self.csv_download_url
        csv_file = mlc.FileObject(ctx=context, 
            id=self.id+'.csv',
            name=self.name+'.csv',
            content_url=content_url,
            encoding_formats=[mlc.EncodingFormat.CSV]
        )
        distribution.append(csv_file)
        # parquet distribution
        metadata.distribution = distribution
        content_url = self.parquet_download_url
        parquet_file = mlc.FileObject(ctx=context, 
            id=self.id+'.parquet',
            name=self.name+'.parquet',
            content_url=content_url,
            encoding_formats=[mlc.EncodingFormat.PARQUET]
        )
        distribution.append(parquet_file)
        metadata.distribution = distribution
        # fields and record set
        fields = []
        for variable in self.variables.values():
            field = mlc.Field(ctx=context,
                id=variable.id,
                name=variable.name,
                description=variable.label,
                source=mlc.Source(file_object=csv_file.id, extract=mlc.Extract(ctx=context, column=variable.name))
            )
            field.data_types.append(variable.croissant_data_type)
            if include_codes:
                # add reference to classification enum
                if variable.classification_id:
                    field.references = mlc.Source(      
                        file_object="{classification.id}_codes"
                    )
            fields.append(field)
        record_set = mlc.RecordSet(id=self.id, fields=fields) 
        record_sets = [record_set]

        if include_codes:
            # classifications
            for classification in self.classifications.values():
                # create a record set for each classification with embedded data
                classification_id = f"{classification.id}_codes"
                value_field_id = f"{classification_id}/value"
                label_field_id = f"{classification_id}/label"
                fields = [
                    mlc.Field(ctx=context, id=value_field_id, description="Value"),
                    mlc.Field(ctx=context, id=label_field_id, name="label", description="Label"),
                ]
                # codes
                classification_records = []
                code_count = 0
                for code in classification.codes:
                    code_count += 1
                    classification_records.append({
                        value_field_id: code.code_value,
                        label_field_id: code.name
                    })
                    if code_count >= max_codes:
                        break
                # create record set
                classification_record_set = mlc.RecordSet(id=classification_id, fields=fields)
                classification_record_set.description = "Code values and labels for fields referencing this record set."
                if classification.code_count <= max_codes:
                    # complete data
                    classification_record_set.data = classification_records
                else:
                    # partial data
                    classification_record_set.examples = classification_records
                    classification_record_set.description += f" This is partial list. The full set contains {classification.code_count} codes."
                record_sets.append(classification_record_set)
        # add record sets to metadata
        metadata.record_sets = record_sets
        return metadata
    
    def get_ddi_codebook(self, include_variables=True, include_statistics=True):
        return self._catalog.get_ddi_codebook(self.id, include_variables, include_statistics)

    def get_import_configuration(self, file_info):
        return self._catalog.get_import_configuration(self.uri, file_info)
    
    def get_postman_collection(self):
        return self._catalog.get_postman_collection(self.id)
    
    def get_variable_by_uri(self, uri):
        for variable in self.variables:
            if variable.uri == uri:
                return variable
    
    def get_variable_by_id(self, id):
        return self.variables.get(id)

    def resolve_classifications(self):
        for classification in self.classifications:
            if isinstance(classification, MtnaRdsClassificationStub):
                classification.resolve()

    def resolve_variables(self):
        for variable in self.variables:
            if isinstance(variable, MtnaRdsVariableStub):
                variable.resolve()

"""
Wrapper class for a variable
"""        
class MtnaRdsVariableStub(MtnaRdsResource):
    classification_id: str | None = Field(alias="classificationId", default=None)
    classification_uri: str | None = Field(alias="classificationUri", default=None)
    data_type: str | None = Field(alias="dataType", default=None)
    is_dimension: bool | None = Field(alias="isDimension", default=None)
    is_measure: bool | None = Field(alias="isMeasure", default=None)
    is_required: bool | None = Field(alias="isRequired", default=None)
    is_weight: bool | None = Field(alias="isWeight", default=None)
    label: str | None = None
    last_update: str | None = Field(alias="lastUpdate", default=None)
    storage_type: str | None = Field(alias="storageType", default=None)

    _data_product: MtnaRdsDataProduct = PrivateAttr(default=None) # This is set by the data product @root_validator or programmatically

    @property
    def croissant_data_type(self):
        # https://dev.socrata.com/docs/datatypes
        if self.data_type == 'NUMERIC':
            return mlc.DataType.FLOAT
        return mlc.DataType.TEXT

    @computed_field
    @property
    def is_stub(self) -> bool:
        return not isinstance(self, MtnaRdsVariable)
    
    def resolve(self) -> "MtnaRdsVariable":
        """
        Converts the stub into a detailed variable
        """
        url = f"catalog/{self._data_product._catalog.id}/{self._data_product.id}/variable/{self.id}"
        response = self._data_product._catalog._server.api_request(url)
        if response.status_code == 200:
            data = response.json()
            variable = MtnaRdsVariable(_data_product=self._data_product, **data)
            self._data_product._variables[variable.id] = variable
            return variable
        else:
            logging.error(f"Could not get variable: {response.status_code}")
            return None

"""
Wrapper class for a variable
"""        
class MtnaRdsVariable(MtnaRdsVariableStub):
    decimals: int | None = None
    end_position: int | None = Field(alias="endPosition", default=None)
    fixed_storage_width: int | None = Field(alias="fixedStorageWidth", default=None)
    format: str | None = None
    index: int | None = None
    start_position: int | None = Field(alias="startPosition", default=None)

    def resolve(self):
        # already resolved, do nothing (overrides stub method)
        return self

class MtnaRdsClassificationStub(MtnaRdsResource):
    reference: bool | None = None
    revision_number: int | None = Field(alias="revisionNumber", default=None)
    code_count: int | None = Field(serialization_alias="codeCount", validation_alias=AliasChoices('codeCount', 'rootCodeCount'), default=None)
    
    _data_product: MtnaRdsDataProduct = PrivateAttr(default=None) # This is set by the data product @root_validator or programmatically
    # codes are lazy loaded when the underlying property is accessed
    _codes: list["MtnaRdsClassificationCode"] = PrivateAttr(default=None)

    @computed_field
    @property
    def codes(self) -> list["MtnaRdsClassificationCode"]:
        if self._codes is None:
            # get from server
            url = f"catalog/{self._data_product._catalog.id}/{self._data_product.id}/classification/{self.id}/codes"
            response = self._data_product._catalog._server.api_request(url)
            if response.status_code == 200:
                data = response.json()
                self._codes = []
                for item in data:
                    code = MtnaRdsClassificationCode(**item)
                    code._classification = self
                    self._codes.append(code)
            else:
                logging.error(f"Could not get codes for classification {self.id}: {response.status_code}")
        return self._codes

    @computed_field
    @property
    def is_stub(self) -> bool:
        return not isinstance(self, MtnaRdsClassification)

    def resolve(self) -> "MtnaRdsClassification":
        """
        Converts the stub into a detailed classification
        """
        url = f"catalog/{self._data_product._catalog.id}/{self._data_product.id}/classification/{self.id}"
        response = self._data_product._catalog._server.api_request(url)
        if response.status_code == 200:
            data = response.json()
            classification = MtnaRdsClassification(_data_product=self._data_product, **data)
            if self._codes: # transfer the codes if already resolved
                classification._codes = self._codes
                for code in self._codes:
                    code._classification = classification
            self._data_product._classifications[classification.id] = classification
            return classification
        else:
            logging.error(f"Could not resolve classification {self.id}: {response.status_code}")
            return None

class MtnaRdsClassification(MtnaRdsClassificationStub):
    is_private: bool | None = Field(alias="isPrivate", default=None)
    keyword_count: int | None = Field(alias="keywordCount", default=None)
    last_update: str | None = Field(alias="lastUpdate", default=None)
    level_count: int | None = Field(alias="levelCount", default=None)

    def resolve(self):
        # already resolved, do nothing (overrides stub method)
        return self

class MtnaRdsClassificationCode(MtnaRdsResource):
    id: str | None = None # override: codes do not have an id property
    code_value: str | None = Field(alias="codeValue", default=None)
    isPrivate: bool | None = Field(alias="isPrivate", default=None)
    reference: bool | None = None

    _classification: MtnaRdsClassificationStub | MtnaRdsClassification = PrivateAttr(default=None) # This is set by the classification @root_validator or programmatically


class MtnaRdsProcess():
    server: MtnaRdsServer | None = None
    completed: int
    id: str
    failure: str
    method_id: str = Field(alias="methodId")
    method_name: str = Field(alias="methodName")
    resource_name: str = Field(alias="resourceName")
    resource_uri: str = Field(alias="resourceUri")
    status: str
    completion_details: any = Field(alias="completionDetails")

    @computed_field
    @property
    def completed_successfully(self) -> bool:
        return self.completed == 100 and self.status == "COMPLETED"

    @computed_field
    @property
    def failed(self) -> bool:
        return self.completed == 100 and self.status != "COMPLETED"
    
    @computed_field
    @property
    def inprogress(self) -> bool:
        return self.status != "PROCESSING"

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
