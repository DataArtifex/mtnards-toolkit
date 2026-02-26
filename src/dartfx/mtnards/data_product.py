"""Data product model for MTNA RDS datasets."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import mlcroissant as mlc
from markdownify import markdownify
from pydantic import Field, PrivateAttr, computed_field

from .base import MtnaRdsError, MtnaRdsResource
from .classification import MtnaRdsClassification, MtnaRdsClassificationCode, MtnaRdsClassificationStub
from .variable import MtnaRdsVariable, MtnaRdsVariableStub

if TYPE_CHECKING:
    from .catalog import MtnaRdsCatalog


class MtnaRdsDataProduct(MtnaRdsResource):
    abbreviation: str | None = None
    cached: bool | None = None
    doi: bool | None = None
    change_log: list[Any] | None = Field(alias="changeLog", default=None)
    citation: str | None = None
    data_product_type: str | None = Field(alias="dataProductType", default=None)
    is_private: bool | None = Field(alias="isPrivate", default=None)
    keywords: list[str] | None = None
    last_update: str | None = Field(alias="lastUpdate", default=None)
    provenance: str | None = None
    urls: list[str] | None = None

    # This is set by the catalog @root_validator or programmatically
    _catalog: MtnaRdsCatalog = PrivateAttr(default=None)  # type: ignore[assignment]
    # variables and classifications are lazy loaded when underlying property is accessed
    _variables: dict[str, MtnaRdsVariableStub | MtnaRdsVariable] | None = PrivateAttr(default=None)
    _classifications: dict[str, MtnaRdsClassificationStub | MtnaRdsClassification] | None = PrivateAttr(default=None)

    @computed_field
    @property
    def api_documentation_url(self) -> str:
        return f"{self._catalog._server.base_url}/swagger/"

    @computed_field
    @property
    def catalog_id(self) -> str:
        return self._catalog.id

    @computed_field
    @property
    def catalog_uri(self) -> str:
        return self._catalog.uri

    @computed_field
    @property
    def classifications(self) -> dict[str, MtnaRdsClassificationStub | MtnaRdsClassification]:
        if self._classifications is None:
            # get from server
            response = self._catalog._server.api_request(f"catalog/{self._catalog.id}/{self.id}/classifications")
            if response.status_code == 200:
                data = response.json()
                self._classifications = {}
                for item in data:
                    classification = MtnaRdsClassificationStub(**item)
                    classification._data_product = self
                    self._classifications[classification.id] = classification
            else:
                raise MtnaRdsError(f"Could not get classifications: {response.status_code}")
        return self._classifications

    @computed_field
    @property
    def count_api_url(self) -> str:
        return f"{self._catalog._server.api_url}/query/{self._catalog.id}/{self.id}/count"

    @computed_field
    @property
    def csv_download_url(self) -> str:
        return f"{self._catalog._server.api_url}/package/{self._catalog.id}/{self.id}.csv"

    @computed_field
    @property
    def explorer_url(self) -> str:
        return f"{self._catalog._server.explorer_url}/explore/{self._catalog.id}/{self.id}/data"

    @computed_field
    @property
    def code_generators_api_url(self) -> str:
        return f"{self._catalog._server.api_url}/snippet/{self._catalog.id}/{self.id}"

    @computed_field
    @property
    def metadata_api_url(self) -> str:
        return f"{self._catalog._server.api_url}/catalog/{self._catalog.id}/{self.id}"

    @computed_field
    @property
    def parquet_download_url(self) -> str:
        return f"{self._catalog._server.api_url}/package/{self._catalog.id}/{self.id}.parquet"

    @computed_field
    @property
    def regression_api_url(self) -> str:
        return f"{self._catalog._server.api_url}/query/{self._catalog.id}/{self.id}/regression"

    @computed_field
    @property
    def select_api_url(self) -> str:
        return f"{self._catalog._server.api_url}/query/{self._catalog.id}/{self.id}/select"

    @computed_field
    @property
    def tabulate_api_url(self) -> str:
        return f"{self._catalog._server.api_url}/query/{self._catalog.id}/{self.id}/tabulate"

    @computed_field
    @property
    def tabengine_url(self) -> str:
        return f"{self._catalog._server.tabengine_url}/tabulation/{self._catalog.id}/{self.id}/custom-tables"

    @computed_field
    @property
    def variables(self) -> dict[str, MtnaRdsVariableStub | MtnaRdsVariable]:
        if self._variables is None:
            # get from server
            response = self._catalog._server.api_request(f"catalog/{self._catalog.id}/{self.id}/variables")
            if response.status_code == 200:
                data = response.json()
                self._variables = {}
                for item in data:
                    variable = MtnaRdsVariableStub(**item)
                    variable._data_product = self
                    self._variables[variable.id] = variable
            else:
                raise MtnaRdsError(f"Could not get variables: {response.status_code}")
        return self._variables

    @computed_field
    @property
    def variables_count(self) -> int:
        return len(self.variables)

    def delete(self) -> Any:
        """Deletes this data product from its catalog."""
        return self._catalog.delete_data_product(self.uri)

    def get_classification_by_uri(self, uri: str) -> MtnaRdsClassificationStub | MtnaRdsClassification | None:
        """Returns a classification by its URI, or ``None`` if not found."""
        for classification in self.classifications.values():
            if classification.uri == uri:
                return classification
        return None

    def get_classification_by_id(self, id: str) -> MtnaRdsClassificationStub | MtnaRdsClassification | None:
        """Returns a classification by its ID, or ``None`` if not found."""
        return self.classifications.get(id)

    def get_classification_variables(
        self, classification: MtnaRdsClassificationStub | MtnaRdsClassification
    ) -> list[MtnaRdsVariableStub | MtnaRdsVariable]:
        """Returns all variables that use the given classification."""
        variables = []
        for variable in self.variables.values():
            if variable.classification_uri == classification.uri:
                variables.append(variable)
        return variables

    def get_croissant(self, include_codes: bool = True, max_codes: int = 100) -> mlc.Metadata:
        """Generates a Croissant ML metadata object for this data product."""
        context = mlc.Context()
        context.is_live_dataset = True
        # metadata
        publishers: list[str] = []
        metadata = mlc.Metadata(
            ctx=context,
            id=self.id,
            name=self.name,
            cite_as=self.citation,
            date_modified=self.last_update,
            keywords=self.keywords,
            publisher=publishers,
            url=self.explorer_url,
            version=self.revision_number or 0,
        )
        if self.description:
            metadata.description = markdownify(self.description)
        # distribution
        distribution = []
        # csv distribution
        content_url = self.csv_download_url
        csv_file = mlc.FileObject(
            ctx=context,
            id=self.id + ".csv",
            name=(self.name or self.id) + ".csv",
            content_url=content_url,
            encoding_formats=[mlc.EncodingFormat.CSV],
        )
        distribution.append(csv_file)
        metadata.distribution = distribution
        # fields and record set
        fields = []
        for variable in self.variables.values():
            field = mlc.Field(
                ctx=context,
                id=variable.id,
                name=variable.name,
                description=variable.label,
                source=mlc.Source(file_object=csv_file.id, extract=mlc.Extract(ctx=context, column=variable.name)),
            )
            field.data_types.append(variable.croissant_data_type)
            if include_codes:
                # add reference to classification enum
                if variable.classification_id:
                    field.references = mlc.Source(id=f"{variable.classification_id}_codes/value")
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
                    mlc.Field(ctx=context, id=value_field_id, name="value", description="The code value"),
                    mlc.Field(ctx=context, id=label_field_id, name="label", description="The code label"),
                ]
                # codes
                classification_records = []
                code_count = 0
                for code in classification.codes:
                    code_count += 1
                    classification_records.append({value_field_id: code.code_value, label_field_id: code.name})
                    if code_count >= max_codes:
                        break
                # create record set
                classification_record_set = mlc.RecordSet(id=classification_id, fields=fields)
                classification_record_set.description = "Code values and labels for fields referencing this record set."
                if classification.code_count is not None and classification.code_count <= max_codes:
                    # complete data
                    classification_record_set.data = classification_records
                else:
                    # partial data
                    classification_record_set.examples = classification_records
                    partial_desc = " This is partial list. The full"
                    partial_desc += f" set contains {classification.code_count} codes."
                    classification_record_set.description += partial_desc
                record_sets.append(classification_record_set)
        # add record sets to metadata
        metadata.record_sets = record_sets
        return metadata

    def get_ddi_codebook(
        self,
        include_variables: bool = True,
        include_statistics: bool = True,
    ) -> bytes:
        """Returns the DDI Codebook XML for this data product."""
        return self._catalog.get_ddi_codebook(self.id, include_variables, include_statistics)

    def get_import_configuration(self, file_info: dict[str, Any]) -> dict[str, Any]:
        """Returns import configuration for uploading data into this product."""
        return self._catalog.get_import_configuration(self.uri, file_info)

    def get_markdown(self, sections: list[str] | None = None, max_codes: int = 10) -> str:
        """Returns the markdown description of the data product."""
        # TODO: upgrade to use Jinja2 templates
        if sections is None:
            sections = []
        self.load_metadata()  # make sure metadata is fully loaded
        # generate
        md = ""
        md += f"# {self.name}\n\n"
        if not sections or "links" in sections:
            explorer_link = f"[Explorer]({self.explorer_url})"
            engine_link = f"[Tabulation Engine]({self.tabengine_url})"
            api_link = f"[API documentation]({self.api_documentation_url})"
            md += f"###### Open in RDS {explorer_link} or {engine_link}. View {api_link}.\n\n"
        if self.description:
            md += f"{markdownify(self.description)}\n\n"
        if not sections or "variables" in sections:
            md += "\n## Variables\n\n"
            md += f"{self.variables_count} variables\n\n"
            md += "| Index | Name | Label | Type | Classification |\n"
            md += "|---|---|---|---|---|\n"
            for variable_index, variable in enumerate(self.variables.values()):
                md += f"| {variable_index} | {variable.name} | {variable.label} | {variable.data_type} "
                if variable.classification_id:
                    cls = variable.classification
                    code_count = cls.code_count if cls else "?"
                    md += f" | {variable.classification_id} ({code_count} codes) |\n"
                else:
                    md += " | - |\n"
        if not sections or "classifications" in sections:
            md += "\n## Classifications\n\n"
            for classification in self.classifications.values():
                md += f"\n### {classification.id}\n\n"
                md += f"{classification.code_count} codes\n\n"
                # Variable names using this classification
                var_names = [
                    variable.name or variable.id for variable in self.get_classification_variables(classification)
                ]
                md += f"Used by: {', '.join(var_names)}\n\n"
                md += "| Code | Label |\n"
                md += "|---|---|\n"
                for code_index, code in enumerate(classification.codes):
                    if code_index >= max_codes:
                        md += f"| ... | ( {len(classification.codes) - max_codes} more) |\n"
                        break
                    md += f"| {code.code_value} | {code.name} |\n"

                md += "\n"
        return md

    def get_postman_collection(self) -> dict[str, Any]:
        """Returns a Postman collection for this data product."""
        return self._catalog.get_postman_collection(self.id)

    def get_variable_by_uri(self, uri: str) -> MtnaRdsVariableStub | MtnaRdsVariable | None:
        """Returns a variable by its URI, or ``None`` if not found."""
        for variable in self.variables.values():
            if variable.uri == uri:
                return variable
        return None

    def get_variable_by_id(self, id: str) -> MtnaRdsVariableStub | MtnaRdsVariable | None:
        """Returns a variable by its ID, or ``None`` if not found."""
        return self.variables.get(id)

    def load_metadata(self) -> None:
        """Loads full metadata (variables and classifications) from the server."""
        # check if metadata is fully loaded
        # note that if one element is not fully loaded, we simply load all of them
        load_variables = False
        if self._variables is not None:
            for variable in self._variables.values():
                if not isinstance(variable, MtnaRdsVariable):
                    load_variables = True
                    break
        else:
            load_variables = True
        load_classifications = False
        if self._classifications is not None:
            for classification in self._classifications.values():
                if not isinstance(classification, MtnaRdsClassification):
                    load_classifications = True
                    break
                if not classification._codes:
                    load_classifications = True
                    break
        else:
            load_classifications = True
        # load metadata if needed
        if load_classifications or load_variables:
            response = self._catalog._server.api_request(f"catalog/{self._catalog.id}/{self.id}/metadata/json")
            if response.status_code == 200:
                metadata = response.json()
                # load classifications
                if load_classifications:
                    if self._classifications is None:
                        self._classifications = {}
                    for metadata_classification in metadata["classifications"]:
                        id = metadata_classification["id"]
                        if id not in self._classifications:
                            classification = MtnaRdsClassificationStub(**metadata_classification)
                            classification._data_product = self
                            self._classifications[id] = classification
                        else:
                            classification = self._classifications[id]
                        # load classification codes if not already loaded
                        if not classification._codes:
                            classification._codes = []
                            for metadata_classification_code in metadata_classification["codes"]:
                                code = MtnaRdsClassificationCode(**metadata_classification_code)
                                code._classification = classification
                                classification._codes.append(code)
                        classification.code_count = len(classification._codes)
                        # This will be in metadata in the future
                # load variables
                if load_variables:
                    if self._variables is None:
                        self._variables = {}
                    for metadata_variable in metadata["recordLayout"]["variables"]:
                        id = metadata_variable["id"]
                        if id not in self._variables:
                            variable = MtnaRdsVariable(**metadata_variable)
                            variable._data_product = self
                            self._variables[id] = variable
                            # classificationId is not in the metadata
                            if variable.classification_uri:
                                # find the classification by uri
                                found = self.get_classification_by_uri(variable.classification_uri)
                                if found is not None:
                                    variable.classification_id = found.id
                        else:
                            variable = self._variables[id]
            else:
                raise MtnaRdsError(f"Could not get metadata: {response.status_code}")
        else:
            logging.debug("Metadata already fully loaded")

    def resolve_classifications(self) -> None:
        """Resolves all classification stubs into full classifications."""
        for classification in list(self.classifications.values()):
            if not isinstance(classification, MtnaRdsClassification):
                classification.resolve()

    def resolve_variables(self) -> None:
        """Resolves all variable stubs into full variables."""
        for variable in list(self.variables.values()):
            if not isinstance(variable, MtnaRdsVariable):
                variable.resolve()
