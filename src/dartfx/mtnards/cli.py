"""Typer-based CLI for MTNA RDS servers."""

import os
import shlex
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, cast

if TYPE_CHECKING:
    from .catalog import MtnaRdsCatalog

import click
import typer
from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from .base import MtnaRdsPatchConflictError
from .server import MtnaRdsServer

# Load .env if present
load_dotenv()

app = typer.Typer(
    name="dartfx-mtnards",
    help="CLI for MTNA RDS servers.",
    rich_markup_mode="rich",
)

console = Console()


@dataclass
class ResourceInfo:
    """Information about a resolved resource path."""

    obj: Any
    catalog_id: str | None = None
    product_id: str | None = None
    variable_id: str | None = None
    property_name: str | None = None
    classification_id: str | None = None
    code_value: str | None = None

    @property
    def type(self) -> str:
        """Return a string identifying the resource type."""
        if self.property_name:
            return "property"
        if self.classification_id:
            return "classification"
        if self.variable_id:
            return "variable"
        if self.product_id:
            return "product"
        if self.catalog_id:
            return "catalog"
        return "root"


class RdsShell:
    """Manages state and execution for the RDS interactive shell."""

    def __init__(self, host: str | None = None, api_key: str | None = None):
        self.host = host
        self.api_key = api_key or os.environ.get("MTNARDS_API_KEY")
        self.catalog_id: str | None = None
        self.product_id: str | None = None
        self._server: MtnaRdsServer | None = None
        self._catalog_cache: dict[str, Any] = {}
        self._product_cache: dict[str, Any] = {}

    @property
    def server(self) -> MtnaRdsServer:
        if self._server is None:
            if not self.host:
                raise ValueError("Not connected to a server. Use 'connect <host>'")
            self._server = MtnaRdsServer(host=self.host, api_key=self.api_key)
        return self._server

    def resolve_path(self, path: str | None) -> ResourceInfo:
        """Resolves a dot-notated path based on current context."""
        path = path or ""

        # 1. Extract property if present
        prop_name = None
        if "@" in path:
            path, prop_name = path.split("@", 1)

        # 2. Handle relative navigation '..'
        if path == "..":
            if self.product_id:
                # Logic for going up
                res = ResourceInfo(obj=None, catalog_id=self.catalog_id)
                res.obj = self.get_catalog(cast(str, self.catalog_id))
                return res
            return ResourceInfo(obj=self.server)

        # 3. Handle absolute path starting with . or /
        is_absolute = path.startswith(".") or path.startswith("/")
        if is_absolute:
            path = path[1:]

        # 4. Extract classification if present
        res_classification_id = None
        if "$" in path:
            path, res_classification_id = path.split("$", 1)

        # 5. Resolve remaining path parts (support both . and /)
        path = path.replace("/", ".")
        parts = path.split(".") if path else []

        # Determine target IDs based on parts and context
        res_cat_id = self.catalog_id
        res_prod_id = self.product_id
        res_var_id = None

        if is_absolute:
            res_cat_id = parts[0] if len(parts) > 0 else None
            res_prod_id = parts[1] if len(parts) > 1 else None
            res_var_id = parts[2] if len(parts) > 2 else None
        else:
            if len(parts) == 3:
                res_cat_id, res_prod_id, res_var_id = parts
            elif len(parts) == 2:
                if self.catalog_id and not self.product_id:
                    res_prod_id, res_var_id = parts
                else:
                    res_cat_id, res_prod_id = parts
            elif len(parts) == 1:
                if self.product_id:
                    res_var_id = parts[0]
                elif self.catalog_id:
                    res_prod_id = parts[0]
                else:
                    res_cat_id = parts[0]

        # Resolve Objects
        obj: Any = self.server
        if res_cat_id:
            obj = self.get_catalog(res_cat_id)
            if res_prod_id:
                obj = obj.get_data_product_by_id(res_prod_id)
                if not obj:
                    raise ValueError(f"Product '{res_prod_id}' not found in catalog '{res_cat_id}'")

                if res_classification_id:
                    classification = obj.get_classification_by_id(res_classification_id)
                    if not classification:
                        raise ValueError(f"Classification '{res_classification_id}' not found")
                    obj = classification
                elif res_var_id:
                    variable = obj.get_variable_by_id(res_var_id)
                    if not variable:
                        raise ValueError(f"Variable '{res_var_id}' not found")
                    obj = variable

        return ResourceInfo(
            obj=obj,
            catalog_id=res_cat_id,
            product_id=res_prod_id,
            variable_id=res_var_id,
            property_name=prop_name,
            classification_id=res_classification_id,
        )

    def get_catalog(self, catalog_id: str) -> "MtnaRdsCatalog":
        if catalog_id not in self._catalog_cache:
            cat = self.server.get_catalog_by_id(catalog_id)
            if not cat:
                raise ValueError(f"Catalog '{catalog_id}' not found")
            self._catalog_cache[catalog_id] = cat
        return self._catalog_cache[catalog_id]

    def _format_private_value(self, value: bool | None) -> str:
        """Formats an isPrivate value for CLI output."""
        if value is True:
            return "yes"
        if value is False:
            return "no"
        return ""

    def do_ls(
        self, path: str | None = None, limit: int = 100, offset: int = 0, count_only: bool = False, codes_limit: int = 0
    ):
        """Context-aware listing with optional path and pagination."""
        try:
            res_info = self.resolve_path(path or "")
            obj = res_info.obj

            if res_info.type == "product":
                # Summary and Listing for product
                var_count = getattr(obj, "variables_count", len(obj.variables))
                class_count = len(obj.classifications)

                if count_only:
                    if res_info.classification_id is not None:
                        console.print(f"Total classifications: {class_count}")
                    else:
                        console.print(f"Total variables: {var_count}")
                    return

                # Determine listing mode
                is_class = res_info.classification_id is not None
                items_dict = obj.classifications if is_class else obj.variables
                items = list(items_dict.values())
                title_prefix = "Classifications" if is_class else "Variables"
                total = class_count if is_class else var_count

                console.print(f"[bold blue]Product:[/bold blue] {obj.id} ({obj.name})")
                console.print(f"  Private: {self._format_private_value(getattr(obj, 'is_private', None))}")
                console.print(f"  Variables: {var_count}")
                console.print(f"  Classifications: {class_count}")

                if items:
                    show_to = min(total, offset + limit)
                    table = Table(title=f"{title_prefix} ({offset + 1}-{show_to}/{total})")
                    table.add_column("ID", style="cyan")
                    table.add_column("Name", style="green")
                    if not is_class:
                        table.add_column("Label")
                        table.add_column("Type", style="dim")
                        table.add_column("Dim", justify="center")
                        table.add_column("Meas", justify="center")
                        table.add_column("Req", justify="center")
                        table.add_column("Wgt", justify="center")
                        table.add_column("Classification")
                        table.add_column("# Codes", justify="right")

                    paged = items[offset : offset + limit]
                    for item in paged:
                        if is_class:
                            table.add_row(item.id, item.name or "")
                        else:
                            # Variable
                            v_type = item.data_type or ""
                            dim = "✓" if item.is_dimension else ""
                            meas = "✓" if item.is_measure else ""
                            req = "✓" if item.is_required else ""
                            wgt = "✓" if item.is_weight else ""

                            cls_ref = self._variable_classification_ref(item)
                            cls_info = cls_ref or ""
                            code_count = ""
                            if cls_ref:
                                try:
                                    cls = item.classification
                                    if cls:
                                        cls_info = cls.id
                                        code_count = str(cls.code_count or 0)
                                        if codes_limit > 0:
                                            codes = cls.codes[:codes_limit]
                                            code_strs = [f"{c.code_value}:{c.name}" for c in codes]
                                            if len(cls.codes) > codes_limit:
                                                code_strs.append("...")
                                            cls_info += f" [{', '.join(code_strs)}]"
                                except Exception:
                                    cls_info += " [error loading codes]"

                            table.add_row(
                                item.id,
                                item.name or "",
                                item.label or "",
                                v_type,
                                dim,
                                meas,
                                req,
                                wgt,
                                cls_info,
                                code_count,
                            )

                    if total > offset + limit:
                        table.add_row("...", f"... and {total - (offset + limit)} more")
                    console.print(table)
                else:
                    console.print(f"[yellow]No {title_prefix.lower()} found in this product.[/yellow]")
                return

            elif res_info.type == "catalog":
                # List products in catalog
                products = obj.data_products or []
                total = len(products)
                if count_only:
                    console.print(f"Total products in {res_info.catalog_id}: {total}")
                    return

                if not products:
                    console.print("No products found.")
                    return

                show_to = min(total, offset + limit)
                table = Table(title=f"Products in {res_info.catalog_id} ({offset + 1}-{show_to}/{total})")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Private")

                paged = products[offset : offset + limit]
                for prod in paged:
                    table.add_row(
                        prod.id, prod.name or "", self._format_private_value(getattr(prod, "is_private", None))
                    )

                if total > offset + limit:
                    table.add_row("...", f"... and {total - (offset + limit)} more")
                console.print(table)

            elif res_info.type == "root":
                # List catalogs
                catalogs = list(self.server.catalogs.values())
                total = len(catalogs)
                if count_only:
                    console.print(f"Total RDS Catalogs: {total}")
                    return

                if not catalogs:
                    console.print("No catalogs found.")
                    return

                show_to = min(total, offset + limit)
                table = Table(title=f"RDS Catalogs ({offset + 1}-{show_to}/{total})")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Private")

                paged = catalogs[offset : offset + limit]
                for cat in paged:
                    table.add_row(cat.id, cat.name or "", self._format_private_value(getattr(cat, "is_private", None)))

                if total > offset + limit:
                    table.add_row("...", f"... and {total - (offset + limit)} more")
                console.print(table)

            elif res_info.type == "classification":
                # List codes for classification
                from .classification import MtnaRdsClassification, MtnaRdsClassificationStub

                if isinstance(obj, (MtnaRdsClassification, MtnaRdsClassificationStub)):
                    total = obj.code_count or len(obj.codes)
                    if count_only:
                        console.print(f"Total codes: {total}")
                        return

                    show_to = min(total, offset + limit)
                    table = Table(title=f"Codes for {res_info.classification_id} ({offset + 1}-{show_to}/{total})")
                    table.add_column("Value", style="cyan")
                    table.add_column("Label", style="green")

                    codes = obj.codes[offset : offset + limit]
                    for code in codes:
                        table.add_row(str(code.code_value), code.name or "")

                    if total > offset + limit:
                        table.add_row("...", f"... and {total - (offset + limit)} more")
                    console.print(table)
                else:
                    console.print("[yellow]Resource is not a classification.[/yellow]")

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")

    def do_cd(self, path: str | None = None):
        """Navigate the hierarchy."""
        if not path:
            self.catalog_id = None
            self.product_id = None
            console.print("[green]Returned to root.[/green]")
            return

        if path == "..":
            if self.product_id:
                self.product_id = None
            elif self.catalog_id:
                self.catalog_id = None
            return

        # Resolve path
        try:
            res_info = self.resolve_path(path)
            if res_info.variable_id or res_info.classification_id:
                console.print("[yellow]Cannot cd into a variable or classification context.[/yellow]")
            elif res_info.product_id:
                self.catalog_id = res_info.catalog_id
                self.product_id = res_info.product_id
                console.print(f"[green]Context: {self.catalog_id}/{self.product_id}[/green]")
            elif res_info.catalog_id:
                self.catalog_id = res_info.catalog_id
                self.product_id = None
                console.print(f"[green]Context: {self.catalog_id}[/green]")
            else:
                self.catalog_id = None
                self.product_id = None
                console.print("[green]Context: (root)[/green]")
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")

    def _json_data_for_current_resource(self, obj: Any) -> Any:
        """Return shallow JSON data for the currently selected resource.

        Excluding computed fields avoids resolving linked resources such as the
        parent catalog, server-derived URLs, variables, or classifications.
        """
        if hasattr(obj, "model_dump"):
            return obj.model_dump(by_alias=True, exclude_computed_fields=True)
        if isinstance(obj, (dict, list)):
            return obj
        return {"value": str(obj)}

    def do_show(
        self,
        path: str | None = None,
        limit: int = 100,
        offset: int = 0,
        codes_limit: int = 0,
        as_json: bool = False,
    ):
        """Show resource details or specific property."""
        try:
            res_info = self.resolve_path(path or "")
            obj = res_info.obj

            if as_json:
                from rich.json import JSON

                if res_info.property_name:
                    val = getattr(obj, res_info.property_name, None)
                    if val is None and hasattr(obj, "model_dump"):
                        val = self._json_data_for_current_resource(obj).get(res_info.property_name)
                    if val is None and hasattr(obj, "dict"):
                        val = obj.dict().get(res_info.property_name)
                    console.print(JSON.from_data(val))
                    return

                console.print(JSON.from_data(self._json_data_for_current_resource(obj)))
                return

            if res_info.property_name:
                # Show specific property
                val = getattr(obj, res_info.property_name, None)
                if val is None:
                    # try dictionary access if it's a model
                    if hasattr(obj, "dict"):
                        val = obj.dict().get(res_info.property_name)
                    elif hasattr(obj, "model_dump"):
                        val = obj.model_dump().get(res_info.property_name)

                if val is not None:
                    if isinstance(val, (dict, list)):
                        from rich.json import JSON

                        console.print(Panel(JSON.from_data(val), title=f"Property: {res_info.property_name}"))
                    else:
                        console.print(Panel(str(val), title=f"Property: {res_info.property_name}"))
                else:
                    console.print(f"[yellow]Property '{res_info.property_name}' not found.[/yellow]")
            elif res_info.type == "product":
                # Specialized product summary
                grid = Table.grid(padding=(0, 1))
                grid.add_column(style="bold cyan", no_wrap=True)
                grid.add_column()
                grid.add_row("ID: ", obj.id)
                grid.add_row("Name: ", obj.name or "")
                if getattr(obj, "label", None):
                    grid.add_row("Label: ", obj.label)
                grid.add_row("Variables: ", str(getattr(obj, "variables_count", 0)))
                grid.add_row("Classifications: ", str(len(obj.classifications)))
                if getattr(obj, "description", None):
                    desc = obj.description
                    if len(desc) > 300:
                        desc = desc[:297] + "..."
                    grid.add_row("Description: ", desc)
                console.print(Panel(grid, title=f"Product Details: {obj.id}", expand=False))
            elif res_info.type == "catalog":
                # Specialized catalog summary
                grid = Table.grid(padding=(0, 1))
                grid.add_column(style="bold green", no_wrap=True)
                grid.add_column()
                grid.add_row("ID: ", obj.id)
                grid.add_row("Name: ", obj.name or "")
                grid.add_row("Products: ", str(len(obj.data_products or [])))
                if getattr(obj, "description", None):
                    grid.add_row("Description: ", obj.description)
                console.print(Panel(grid, title=f"Catalog Details: {obj.id}", expand=False))
            elif res_info.type == "variable":
                # Specialized variable summary
                from .variable import MtnaRdsVariable, MtnaRdsVariableStub

                if isinstance(obj, (MtnaRdsVariable, MtnaRdsVariableStub)):
                    grid = Table.grid(padding=(0, 1))
                    grid.add_column(style="bold cyan", no_wrap=True)
                    grid.add_column()
                    grid.add_row("ID: ", obj.id)
                    grid.add_row("Name: ", obj.name or "")
                    grid.add_row("Label: ", obj.label or "")
                    grid.add_row("Type: ", obj.data_type or "N/A")

                    cls_ref = self._variable_classification_ref(obj)
                    if cls_ref:
                        try:
                            cls = obj.classification
                            if cls:
                                codes_total = cls.code_count or len(cls.codes)
                                grid.add_row("Classification: ", f"{cls.id} ({codes_total} codes)")
                        except Exception:
                            grid.add_row("Classification: ", f"{cls_ref} [error loading]")

                    console.print(Panel(grid, title=f"Variable Details: {obj.id}", expand=False))

                    # Show codes table if requested
                    if cls_ref and codes_limit > 0:
                        try:
                            cls = obj.classification
                            if cls:
                                table = Table(title=f"Classification Codes: {cls.id}")
                                table.add_column("Value", style="cyan")
                                table.add_column("Label", style="green")
                                for c in cls.codes[:codes_limit]:
                                    table.add_row(str(c.code_value), c.name or "")
                                if len(cls.codes) > codes_limit:
                                    table.add_row("...", f"... and {len(cls.codes) - codes_limit} more")
                                console.print(table)
                        except Exception:
                            console.print("[red]Error loading codes table.[/red]")
                else:
                    console.print("[yellow]Resource is not a variable.[/yellow]")
            elif res_info.type == "classification":
                # Specialized classification summary
                from .classification import MtnaRdsClassification, MtnaRdsClassificationStub

                if isinstance(obj, (MtnaRdsClassification, MtnaRdsClassificationStub)):
                    grid = Table.grid(padding=(0, 1))
                    grid.add_column(style="bold yellow", no_wrap=True)
                    grid.add_column()
                    grid.add_row("ID: ", obj.id)
                    grid.add_row("Name: ", obj.name or "")
                    total = obj.code_count or len(obj.codes)
                    grid.add_row("Codes: ", str(total))

                    console.print(Panel(grid, title=f"Classification Details: {obj.id}", expand=False))

                    # Show paged codes
                    if total > 0:
                        show_to = min(total, offset + limit)
                        table = Table(title=f"Codes ({offset + 1}-{show_to}/{total})")
                        table.add_column("Value", style="cyan")
                        table.add_column("Label", style="green")

                        codes = obj.codes[offset : offset + limit]
                        for code in codes:
                            table.add_row(str(code.code_value), code.name or "")

                        if total > offset + limit:
                            table.add_row("...", f"... and {total - (offset + limit)} more")
                        console.print(table)
                else:
                    console.print("[yellow]Resource is not a classification.[/yellow]")
            else:
                # Generic fallback with JSON support
                content: Any = str(obj)
                title = f"Details: {res_info.type}"

                try:
                    if hasattr(obj, "model_dump"):
                        from rich.json import JSON

                        content = JSON.from_data(obj.model_dump())
                    elif isinstance(obj, (dict, list)):
                        from rich.json import JSON

                        content = JSON.from_data(obj)
                except Exception:
                    pass

                console.print(Panel(content, title=title))

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")

    def do_set(self, path: str, value: str | None = None, edit: bool = False):
        """Set a resource property."""
        try:
            res_info = self.resolve_path(path)
            if not res_info.property_name:
                console.print("[red]Error: Must specify a property using @ (e.g., path@label)[/red]")
                return

            if edit:
                current_val = getattr(res_info.obj, res_info.property_name, "") or ""
                value = click.edit(str(current_val))
                if value is None:
                    console.print("Edit cancelled.")
                    return
                value = value.strip()

            if value is None:
                console.print("[red]Error: Value required or use --edit[/red]")
                return

            if res_info.classification_id is not None:
                console.print("[red]Error:[/red] Classification properties are not patchable from the CLI.")
                return

            target = res_info.obj
            if not hasattr(target, "patch"):
                console.print("[red]Error:[/red] This resource does not support patching.")
                return

            updates = {res_info.property_name: value}
            target.patch(updates)
            console.print(f"[green]Updated[/green] {path} = '{value}'")

        except MtnaRdsPatchConflictError as e:
            console.print(f"[red]Patch conflict:[/red] {e}")

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")

    def do_stats(self, path: str | None = None):
        """Show statistical summary for a resource."""
        try:
            res_info = self.resolve_path(path or "")
            console.print(f"[yellow]Stub: Statistical summary for {res_info.type}[/yellow]")
            # Logic here would aggregate metrics or call a stats API
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")

    def do_refresh(self, path: str | None = None):
        """Clear cached context and reload server/catalog/product metadata."""
        try:
            if self._server is None and not self.host:
                raise ValueError("Not connected to a server. Use 'connect <host>'")

            # Reset local shell caches so subsequent lookups use fresh metadata.
            self._catalog_cache.clear()
            self._product_cache.clear()

            res_info = self.resolve_path(path or "")

            # Always refresh the root catalog index first.
            self.server.refresh_catalogs()

            if res_info.type == "root":
                console.print("[green]Refreshed[/green] server catalog index")
                return

            if res_info.catalog_id is None:
                console.print("[yellow]No catalog context to refresh.[/yellow]")
                return

            catalog = self.server.get_catalog_by_id(res_info.catalog_id, fetch=True)
            if catalog is None:
                raise ValueError(f"Catalog '{res_info.catalog_id}' not found")
            self._catalog_cache[catalog.id] = catalog

            if res_info.product_id is None:
                console.print(f"[green]Refreshed[/green] catalog metadata: {catalog.id}")
                return

            product = catalog.get_data_product_by_id(res_info.product_id)
            if product is None:
                raise ValueError(f"Product '{res_info.product_id}' not found in catalog '{catalog.id}'")

            product.load_metadata()
            self._product_cache[f"{catalog.id}.{product.id}"] = product
            console.print(f"[green]Refreshed[/green] product metadata: {catalog.id}.{product.id}")

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")

    def do_import_ddic(self, xml_path: str):
        """Upload and import a DDI Codebook XML file to the current data product."""
        catalog_id = self.catalog_id
        product_id = self.product_id
        if not catalog_id or not product_id:
            console.print(
                "[red]Error: Command 'import-ddic' is only available within a data product context.[/red]\n"
                "Navigate to a product first (e.g. cd <catalog_id>/<product_id>)"
            )
            return

        try:
            catalog = self.server.get_catalog_by_id(catalog_id, fetch=True)
            if not catalog:
                console.print(f"[red]Error: Current catalog {catalog_id} not found on server.[/red]")
                return
            product = catalog.get_data_product_by_id(product_id)
            if not product:
                console.print(f"[red]Error: Current product {product_id} not found in catalog.[/red]")
                return

            console.print(
                f"Importing metadata from [cyan]{xml_path}[/cyan] into product [magenta]{product.id}[/magenta]..."
            )
            from .utils import import_ddic_metadata

            completed_job = import_ddic_metadata(product, xml_path)
            console.print(f"[green]Success:[/green] Metadata import complete. Status: {completed_job.status}")

        except Exception as e:
            console.print(f"[red]Error during import:[/red] {e}")

    def do_import_rdsjson(self, json_path: str):
        """Upload and import a native RDS JSON metadata file to the current data product."""
        catalog_id = self.catalog_id
        product_id = self.product_id
        if not catalog_id or not product_id:
            console.print(
                "[red]Error: Command 'import-rdsjson' is only available within a data product context.[/red]\n"
                "Navigate to a product first (e.g. cd <catalog_id>/<product_id>)"
            )
            return

        try:
            catalog = self.server.get_catalog_by_id(catalog_id, fetch=True)
            if not catalog:
                console.print(f"[red]Error: Current catalog {catalog_id} not found on server.[/red]")
                return
            product = catalog.get_data_product_by_id(product_id)
            if not product:
                console.print(f"[red]Error: Current product {product_id} not found in catalog.[/red]")
                return

            console.print(
                f"Importing JSON metadata from [cyan]{json_path}[/cyan] into product [magenta]{product.id}[/magenta]..."
            )
            from .utils import import_metadata_rdsjson_workflow

            completed_job = import_metadata_rdsjson_workflow(product, json_path)
            console.print(f"[green]Success:[/green] JSON metadata import complete. Status: {completed_job.status}")

        except Exception as e:
            console.print(f"[red]Error during JSON metadata import:[/red] {e}")

    def do_export_rdsjson(self, output_path: str):
        """Retrieve and save the DataProductImportConfiguration JSON for the current data product."""
        catalog_id = self.catalog_id
        product_id = self.product_id
        if not catalog_id or not product_id:
            console.print(
                "[red]Error: Command 'export-rdsjson' is only available within a data product context.[/red]\n"
                "Navigate to a product first (e.g. cd <catalog_id>/<product_id>)"
            )
            return

        try:
            catalog = self.server.get_catalog_by_id(catalog_id, fetch=True)
            if not catalog:
                console.print(f"[red]Error: Current catalog {catalog_id} not found on server.[/red]")
                return
            product = catalog.get_data_product_by_id(product_id)
            if not product:
                console.print(f"[red]Error: Current product {product_id} not found in catalog.[/red]")
                return

            console.print(f"Retrieving JSON import configuration for product [magenta]{product.id}[/magenta]...")
            config = product.get_metadata_rdsjson_config()

            import json
            from pathlib import Path

            path_obj = Path(output_path)
            with path_obj.open("w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            console.print(f"[green]Success:[/green] Saved JSON config to [cyan]{output_path}[/cyan]")

        except Exception as e:
            console.print(f"[red]Error retrieving JSON config:[/red] {e}")

    def do_search(self, pattern: str):
        """Search metadata for a pattern."""
        console.print(f"[yellow]Stub: Searching metadata for '{pattern}'[/yellow]")

    def do_export(self, path: str | None = None, format: str = "croissant"):
        """Export tool documentation to a standard format."""
        try:
            res_info = self.resolve_path(path or "")
            console.print(f"[yellow]Stub: Exporting {res_info.type} to {format}[/yellow]")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")

    def do_create(self, resource_type: str, name: str):
        """Create a new resource (requires confirmation)."""
        if Confirm.ask(f"Create new {resource_type} '{name}'?"):
            console.print(f"[yellow]Stub: Creating {resource_type} '{name}'[/yellow]")

    def do_delete(self, path: str):
        """Delete a resource (requires confirmation)."""
        try:
            res_info = self.resolve_path(path)

            # Constraint: Deleting a product is only allowed from catalog context (not from within the product)
            if res_info.type == "product" and self.product_id:
                console.print(
                    "[yellow]Safety check: Cannot delete a product while you are inside a product context.[/yellow]\n"
                    "Navigate up to the catalog level first: [bold]cd ..[/bold]"
                )
                return

            if Confirm.ask(f"[red]CRITICAL:[/red] Delete {res_info.type} '{path}'?"):
                console.print(f"[yellow]Stub: Deleting {path}[/yellow]")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")

    def do_run(self, script_path: str):
        """Run a RDS script file."""
        path = Path(script_path)
        if not path.exists():
            console.print(f"[red]Script not found:[/red] {script_path}")
            return

        console.print(f"[bold blue]Running script:[/bold blue] {script_path}")
        with path.open("r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                console.print(f"[blue]>[/blue] [dim]{line}[/dim]")
                self.execute_line(line)
        console.print("[bold green]Script finished.[/bold green]")

    def do_api(self, limit: int = 100):
        """Display API call history."""
        history = self.server.api_history
        if not history:
            console.print("[yellow]No API calls recorded yet.[/yellow]")
            return

        # Show most recent first
        display_history = list(reversed(history))[:limit]

        table = Table(title=f"API Call History (Most Recent {len(display_history)})")
        table.add_column("#", justify="right", style="dim")
        table.add_column("Time", style="dim")
        table.add_column("Method", style="bold cyan")
        table.add_column("Path", style="green")
        table.add_column("Status", justify="right")
        table.add_column("Duration (s)", justify="right", style="yellow")

        for i, entry in enumerate(display_history, 1):
            idx = len(history) - i + 1
            status = str(entry["status"])
            status_color = "green" if entry["status"] < 400 else "red"

            # Format timestamp
            t = time.strftime("%H:%M:%S", time.localtime(entry["timestamp"]))

            # Make path clickable if url is present
            path_display = entry["path"]
            if "url" in entry:
                path_display = f"[link={entry['url']}]{entry['path']}[/link]"

            table.add_row(
                str(idx),
                t,
                entry["method"],
                path_display,
                f"[{status_color}]{status}[/{status_color}]",
                f"{entry['duration']:.3f}",
            )

        console.print(table)
        avg_duration = sum(e["duration"] for e in history) / len(history)
        console.print(f"[dim]Total calls: {len(history)} | Average duration: {avg_duration:.3f}s[/dim]")

    def _parse_set_value(self, cmd_args: list[str]) -> tuple[str | None, bool]:
        """Parse the set command value, joining unquoted trailing tokens."""
        edit = "--edit" in cmd_args
        value_parts = [arg for arg in cmd_args[1:] if arg != "--edit"]
        value = " ".join(value_parts) if value_parts else None
        return value, edit

    def execute_line(self, line: str) -> bool:
        """Execute a single command line. Returns False if shell should exit."""
        line = line.strip()
        if not line or line.startswith("#"):
            return True

        try:
            parts = shlex.split(line)
            if not parts:
                return True
            cmd = parts[0].lower()
            cmd_args = parts[1:]

            if cmd in ["exit", "quit"]:
                return False
            elif cmd == "connect":
                self.host = cmd_args[0] if cmd_args else os.environ.get("MTNARDS_HOST")
                self._server = None  # Force reconnect
                console.print(f"Connected to {self.host}")
            elif cmd == "ls":
                limit = int(self._extract_param(cmd_args, "--limit", "-l") or 100)
                offset = int(self._extract_param(cmd_args, "--offset", "-o") or 0)
                count = "--count" in cmd_args or "-n" in cmd_args

                codes_limit_raw = self._extract_param(cmd_args, "--codes", "-c")
                if codes_limit_raw is None and self._has_param(cmd_args, "--codes", "-c"):
                    codes_limit = 10
                else:
                    codes_limit = int(codes_limit_raw or 0)

                path_arg = next((a for a in cmd_args if not a.startswith("-")), None)
                self.do_ls(path=path_arg, limit=limit, offset=offset, count_only=count, codes_limit=codes_limit)
            elif cmd == "cd":
                self.do_cd(cmd_args[0] if cmd_args else None)
            elif cmd in ["show", "get"]:
                path_arg = next((a for a in cmd_args if not a.startswith("-")), None)
                limit = int(self._extract_param(cmd_args, "--limit", "-l") or 100)
                offset = int(self._extract_param(cmd_args, "--offset", "-o") or 0)
                as_json = self._has_param(cmd_args, "--json", "-j")

                codes_limit_raw = self._extract_param(cmd_args, "--codes", "-c")
                if codes_limit_raw is None and self._has_param(cmd_args, "--codes", "-c"):
                    codes_limit = 10
                else:
                    codes_limit = int(codes_limit_raw or 0)

                self.do_show(path=path_arg, limit=limit, offset=offset, codes_limit=codes_limit, as_json=as_json)
            elif cmd == "set":
                if not cmd_args:
                    console.print("[yellow]Usage: set <path@property> [value] [--edit][/yellow]")
                    return True
                path = cmd_args[0]
                val, edit = self._parse_set_value(cmd_args)
                self.do_set(path, val, edit=edit)
            elif cmd == "run":
                if not cmd_args:
                    console.print("[yellow]Usage: run <script_path>[/yellow]")
                    return True
                self.do_run(cmd_args[0])
            elif cmd in ["variables", "vars"]:
                if not self.product_id:
                    console.print("[yellow]Command 'variables' is only available in product context.[/yellow]")
                    return True
                limit = int(self._extract_param(cmd_args, "--limit", "-l") or 100)
                offset = int(self._extract_param(cmd_args, "--offset", "-o") or 0)

                codes_limit_raw = self._extract_param(cmd_args, "--codes", "-c")
                if codes_limit_raw is None and self._has_param(cmd_args, "--codes", "-c"):
                    codes_limit = 10
                else:
                    codes_limit = int(codes_limit_raw or 0)

                self.do_ls(path="", limit=limit, offset=offset, codes_limit=codes_limit)
            elif cmd in ["classifications", "cls"]:
                if not self.product_id:
                    console.print(
                        "[yellow]Command 'cls' (classifications) is only available in product context.[/yellow]"
                    )
                    return True
                limit = int(self._extract_param(cmd_args, "--limit", "-l") or 100)
                offset = int(self._extract_param(cmd_args, "--offset", "-o") or 0)
                self.do_ls(path="$", limit=limit, offset=offset)
            elif cmd == "stats":
                if not self.product_id:
                    console.print("[yellow]Command 'stats' is only available in product context.[/yellow]")
                    return True
                self.do_stats(cmd_args[0] if cmd_args else None)
            elif cmd == "refresh":
                path_arg = next((a for a in cmd_args if not a.startswith("-")), None)
                self.do_refresh(path_arg)
            elif cmd == "api":
                limit = int(self._extract_param(cmd_args, "--limit", "-l") or 100)
                self.do_api(limit=limit)
            elif cmd == "search":
                if not cmd_args:
                    console.print("[yellow]Usage: search <pattern>[/yellow]")
                    return True
                self.do_search(cmd_args[0])
            elif cmd == "import-ddic":
                if not cmd_args:
                    console.print("[yellow]Usage: import-ddic <ddi_xml_path>[/yellow]")
                    return True
                self.do_import_ddic(cmd_args[0])
            elif cmd == "import-rdsjson":
                if not cmd_args:
                    console.print("[yellow]Usage: import-rdsjson <json_path>[/yellow]")
                    return True
                self.do_import_rdsjson(cmd_args[0])
            elif cmd == "export-rdsjson":
                if not cmd_args:
                    console.print("[yellow]Usage: export-rdsjson <output_path>[/yellow]")
                    return True
                self.do_export_rdsjson(cmd_args[0])
            elif cmd == "export":
                if not self.product_id:
                    console.print("[yellow]Command 'export' is only available in product context.[/yellow]")
                    return True
                fmt = self._extract_param(cmd_args, "--format", "-f") or "croissant"
                path = next((a for a in cmd_args if not a.startswith("-")), cast(Any, None))
                self.do_export(path, format=fmt)
            elif cmd == "create":
                if len(cmd_args) < 2:
                    console.print("[yellow]Usage: create <type> <name>[/yellow]")
                    return True
                self.do_create(cmd_args[0], cmd_args[1])
            elif cmd == "delete":
                if not cmd_args:
                    console.print("[yellow]Usage: delete <path>[/yellow]")
                    return True
                self.do_delete(cmd_args[0])
            elif cmd == "whoami":
                console.print(f"Server: {self.host}")
                console.print(f"API Key: {self.api_key or 'None'}")
            elif cmd == "debug":
                mode = cmd_args[0].lower() if cmd_args else "toggle"

                if mode == "verbose":
                    verbose_mode = cmd_args[1].lower() if len(cmd_args) > 1 else "toggle"
                    if verbose_mode in ["on", "true", "1"]:
                        self.server.debug_verbose = True
                    elif verbose_mode in ["off", "false", "0"]:
                        self.server.debug_verbose = False
                    else:
                        self.server.debug_verbose = not self.server.debug_verbose
                    state = "[green]ON[/green]" if self.server.debug_verbose else "[red]OFF[/red]"
                    console.print(f"Verbose debug mode: {state}")
                    return True

                if mode in ["on", "true", "1"]:
                    self.server.debug = True
                elif mode in ["off", "false", "0"]:
                    self.server.debug = False
                else:
                    self.server.debug = not self.server.debug
                state = "[green]ON[/green]" if self.server.debug else "[red]OFF[/red]"
                console.print(f"Debug mode: {state}")
            elif cmd == "help":
                self.do_help()
            elif cmd == "clear":
                console.clear()
            else:
                console.print(f"[red]Unknown command: {cmd}[/red]")
        except Exception as e:
            console.print(f"[red]Error executing command:[/red] {e}")

        return True

    def _extract_param(self, args, name, short=None):
        """Helper to extract --param or -p from command args."""
        try:
            for idx, arg in enumerate(args):
                if arg == name or (short and arg == short):
                    if idx + 1 < len(args):
                        # Make sure next arg isn't another flag
                        if not args[idx + 1].startswith("-"):
                            return args[idx + 1]
        except (ValueError, IndexError):
            pass
        return None

    def _has_param(self, args, name, short=None):
        """Helper to check if a flag exists in command args."""
        for arg in args:
            if arg == name or (short and arg == short):
                return True
        return False

    def _variable_classification_ref(self, variable: Any) -> str | None:
        """Returns best available classification reference for a variable.

        Prefer classification id when available, otherwise use canonical uri,
        resolving uri to id when possible.
        """
        cls_id = getattr(variable, "classification_id", None)
        if cls_id:
            return str(cls_id)

        cls_uri = getattr(variable, "classification_uri", None)
        if not cls_uri:
            return None

        try:
            cls = getattr(variable, "classification", None)
            if cls is not None and getattr(cls, "id", None):
                return str(cls.id)
        except Exception:
            pass

        return str(cls_uri)

    def do_help(self):
        """Show context-sensitive commands."""
        # 1. Common Commands
        common = Table(title="Common Commands", show_header=True, box=None)
        common.add_column("Command", style="cyan")
        common.add_column("Usage/Description")
        common.add_row("ls", "ls [path] [-l N] [-o M] [-n]")
        common.add_row("cd", "cd <path> (use .. to go up, . for root)")
        common.add_row("show", "show [path][@property] [--json|-j]")
        common.add_row("refresh", "refresh [path] (reload context metadata)")
        common.add_row("whoami", "Show connection and API key info")
        common.add_row("run", "run <script_path>")
        common.add_row("api", "Show API call history and timing")
        common.add_row("debug", "Toggle debug mode (on/off)")
        common.add_row("debug verbose", "Toggle verbose HTTP debug details")
        common.add_row("exit", "Exit session")

        # 2. Context Commands
        context_title = "Global Management"
        style = "bold magenta"
        if self.product_id:
            context_title = f"Product: {self.product_id}"
            style = "bold blue"
        elif self.catalog_id:
            context_title = f"Catalog: {self.catalog_id}"
            style = "bold green"

        ctx_table = Table(title=context_title, title_style=style, show_header=True)
        ctx_table.add_column("Command", style="green")
        ctx_table.add_column("Description")

        if self.product_id:
            ctx_table.add_row("variables", "List variables in current product")
            ctx_table.add_row("classifications", "List classifications (using $ shortcut)")
            ctx_table.add_row("set", "Update metadata (e.g. set @description '...')")
            ctx_table.add_row("stats", "Show statistical summary (if available)")
            ctx_table.add_row("export", "Generate documentation (croissant, dcat)")
            ctx_table.add_row("import-ddic", "Upload and import DDI-C XML metadata")
            ctx_table.add_row("import-rdsjson", "Upload and import native RDS JSON metadata")
            ctx_table.add_row("export-rdsjson", "Retrieve and save DataProductImportConfiguration JSON")
            ctx_table.add_row("delete", "Delete this product")
        elif self.catalog_id:
            ctx_table.add_row("search", "Search for products in this catalog")
            ctx_table.add_row("set", "Patch catalog/product metadata (e.g. set @name '...')")
            ctx_table.add_row("create", "create product <name>")
            ctx_table.add_row("delete", "Delete this catalog")
        else:  # Root
            ctx_table.add_row("search", "Global search for catalogs/products")
            ctx_table.add_row("set", "Patch metadata by full path (e.g. set cat.prod@name '...')")
            ctx_table.add_row("create", "create catalog <name>")

        console.print("\n", common)
        console.print(ctx_table, "\n")


def get_server(
    host: str | None,
    api_key: str | None = None,
    base_path: str = "rds",
    api_path: str = "api",
) -> MtnaRdsServer:
    """Helper to initialize server connection."""
    if not host:
        console.print("[red]Error:[/red] RDS host is required (use --host or MTNARDS_HOST environment variable)")
        raise typer.Exit(1)

    return MtnaRdsServer(
        host=host,
        api_key=api_key or os.environ.get("MTNARDS_API_KEY"),
        base_path=base_path,
        api_path=api_path,
    )


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    host: Annotated[str | None, typer.Option("--host", "-H", envvar="MTNARDS_HOST", help="RDS server host URL")] = None,
    api_key: Annotated[
        str | None,
        typer.Option("--api-key", "-k", envvar="MTNARDS_API_KEY", help="RDS API key", show_default=False),
    ] = None,
    base_path: Annotated[str, typer.Option("--base-path", help="RDS base path")] = "rds",
    api_path: Annotated[str, typer.Option("--api-path", help="RDS API path")] = "api",
    catalog: Annotated[str | None, typer.Option("--catalog", "-c", help="Initial catalog context", hidden=True)] = None,
    product: Annotated[str | None, typer.Option("--product", "-p", help="Initial product context", hidden=True)] = None,
    path: Annotated[str | None, typer.Option("--path", "-P", help="Initial path context (e.g. cat/prod)")] = None,
):
    """MTNA RDS CLI toolkit."""
    # Store settings in context to be used by subcommands
    ctx.obj = {
        "host": host,
        "api_key": api_key,
        "base_path": base_path,
        "api_path": api_path,
        "path": path or (f"{catalog}.{product}" if catalog and product else catalog),
    }

    if ctx.invoked_subcommand is None:
        if host and api_key:
            _run_shell_impl(ctx)
        else:
            # Show help if host/api_key are missing and no command given
            console.print(ctx.get_help())
            raise typer.Exit()


@app.command()
def info(ctx: typer.Context):
    """Display server information."""
    server = get_server(**ctx.obj)
    try:
        info_data = server.info
        console.print(f"[bold blue]Server Name:[/bold blue] {info_data.name}")
        console.print(f"[bold blue]Version:[/bold blue] {info_data.version}")
        console.print(f"[bold blue]Released:[/bold blue] {info_data.released}")
        console.print(f"[bold blue]API URL:[/bold blue] {server.api_url}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


def _run_shell_impl(ctx: typer.Context):
    """Internal implementation of the interactive shell."""
    host = ctx.obj.get("host")
    api_key = ctx.obj.get("api_key")
    initial_path = ctx.obj.get("path")

    shell_obj = RdsShell(host=host, api_key=api_key)

    # Resolve initial context if requested
    if initial_path:
        try:
            shell_obj.do_cd(initial_path)
        except Exception:
            # Fall back to root if invalid, error already printed by do_cd
            pass

    history_file = os.path.expanduser("~/.mtnards_history")
    session: PromptSession = PromptSession(history=FileHistory(history_file))

    completer = WordCompleter(
        [
            "connect",
            "info",
            "ls",
            "cd",
            "cd ..",
            "show",
            "get",
            "set",
            "variables",
            "vars",
            "classifications",
            "cls",
            "download",
            "import-ddic",
            "import-rdsjson",
            "export-rdsjson",
            "help",
            "exit",
            "quit",
            "clear",
            "context",
            "api",
            "history",
            "stats",
            "search",
        ],
        ignore_case=True,
    )

    console.print(
        Panel(
            "[bold green]Welcome to the MTNA RDS Hierarchical Shell[/bold green]\n"
            "Navigation: [cyan]root / catalog / product[/cyan]\n"
            "Shortcuts: [yellow]@property[/yellow], [yellow]$classification[/yellow], [yellow].dot.notation[/yellow]\n"
            "Type [bold cyan]help[/bold cyan] for commands or [bold red]exit[/bold red] to quit."
        )
    )

    while True:
        try:
            # Build prompt
            prompt_parts = ["[bold yellow]rds[/bold yellow]"]
            if shell_obj.host:
                server_name = shell_obj.host.replace("https://", "").replace("http://", "").split("/")[0]
                prompt_parts.append(f"([dim]{server_name}[/dim])")
            if shell_obj.catalog_id:
                prompt_parts.append(f":[bold cyan]{shell_obj.catalog_id}[/bold cyan]")
            if shell_obj.product_id:
                prompt_parts.append(f"/[bold magenta]{shell_obj.product_id}[/bold magenta]")
            prompt_parts.append("> ")
            prompt_text = "".join(prompt_parts)

            user_input = session.prompt(PromptHTMLWrapper(prompt_text), completer=completer).strip()
            if not user_input:
                continue

            if not shell_obj.execute_line(user_input):
                break

        except KeyboardInterrupt:
            if Confirm.ask("\nExit RDS shell?", default=False):
                break
            continue
        except EOFError:
            break
        except Exception as e:
            console.print(f"[red]Shell Error:[/red] {e}")

    console.print("[bold yellow]Goodbye![/bold yellow]")


@app.command()
def shell(
    ctx: typer.Context,
    path: Annotated[str | None, typer.Option("--path", "-P", help="Initial path context (e.g. cat/prod)")] = None,
):
    """Enter an interactive shell mode."""
    if path:
        ctx.obj["path"] = path
    _run_shell_impl(ctx)


@app.command()
def run(
    ctx: typer.Context,
    script_file: Annotated[typer.FileText, typer.Argument(help="The RDS script file to execute")],
):
    """Run a sequence of commands from a file."""
    host = ctx.obj.get("host")
    api_key = ctx.obj.get("api_key")
    shell_obj = RdsShell(host=host, api_key=api_key)

    for line in script_file:
        shell_obj.execute_line(line)


@app.command(name="import-ddic")
def import_ddic(
    ctx: typer.Context,
    catalog_id: Annotated[str, typer.Argument(help="The ID of the catalog")],
    product_id: Annotated[str, typer.Argument(help="The ID of the data product")],
    xml_path: Annotated[Path, typer.Argument(help="Path to the DDI-C XML file")],
):
    """Upload and import DDI-C XML metadata to a data product."""
    server = get_server(**ctx.obj)
    try:
        catalog = server.get_catalog_by_id(catalog_id, fetch=True)
        if not catalog:
            console.print(f"[red]Error:[/red] Catalog '{catalog_id}' not found.")
            raise typer.Exit(1)
        product = catalog.get_data_product_by_id(product_id)
        if not product:
            console.print(f"[red]Error:[/red] Product '{product_id}' not found.")
            raise typer.Exit(1)

        console.print(
            f"Importing metadata from [cyan]{xml_path}[/cyan] into product [magenta]{product_id}[/magenta]..."
        )
        from .utils import import_ddic_metadata

        completed_job = import_ddic_metadata(product, xml_path)
        console.print(f"[green]Success:[/green] Metadata import complete. Status: {completed_job.status}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


@app.command(name="import-rdsjson")
def import_rdsjson(
    ctx: typer.Context,
    catalog_id: Annotated[str, typer.Argument(help="The ID of the catalog")],
    product_id: Annotated[str, typer.Argument(help="The ID of the data product")],
    json_path: Annotated[Path, typer.Argument(help="Path to the JSON metadata file")],
):
    """Upload and import native RDS JSON metadata to a data product."""
    server = get_server(**ctx.obj)
    try:
        catalog = server.get_catalog_by_id(catalog_id, fetch=True)
        if not catalog:
            console.print(f"[red]Error:[/red] Catalog '{catalog_id}' not found.")
            raise typer.Exit(1)
        product = catalog.get_data_product_by_id(product_id)
        if not product:
            console.print(f"[red]Error:[/red] Product '{product_id}' not found.")
            raise typer.Exit(1)

        console.print(
            f"Importing JSON metadata from [cyan]{json_path}[/cyan] into product [magenta]{product_id}[/magenta]..."
        )
        from .utils import import_metadata_rdsjson_workflow

        completed_job = import_metadata_rdsjson_workflow(product, json_path)
        console.print(f"[green]Success:[/green] JSON metadata import complete. Status: {completed_job.status}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


@app.command(name="export-rdsjson")
def export_rdsjson(
    ctx: typer.Context,
    catalog_id: Annotated[str, typer.Argument(help="The ID of the catalog")],
    product_id: Annotated[str, typer.Argument(help="The ID of the data product")],
    output_path: Annotated[Path, typer.Argument(help="The file path to save the JSON configuration")],
):
    """Retrieve and save the DataProductImportConfiguration JSON for a data product."""
    server = get_server(**ctx.obj)
    try:
        catalog = server.get_catalog_by_id(catalog_id, fetch=True)
        if not catalog:
            console.print(f"[red]Error:[/red] Catalog '{catalog_id}' not found.")
            raise typer.Exit(1)
        product = catalog.get_data_product_by_id(product_id)
        if not product:
            console.print(f"[red]Error:[/red] Product '{product_id}' not found.")
            raise typer.Exit(1)

        console.print(f"Retrieving JSON import configuration for product [magenta]{product_id}[/magenta]...")
        config = product.get_metadata_rdsjson_config()

        import json

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        console.print(f"[green]Success:[/green] Saved JSON config to [cyan]{output_path}[/cyan]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


class PromptHTMLWrapper:
    """Simple wrapper to satisfy prompt_toolkit expectations for rich text prompts."""

    def __init__(self, text):
        self.text = text

    def __call__(self):
        import re

        clean_text = re.sub(r"\[/?.*?\]", "", self.text)
        return clean_text

    def __len__(self):
        import re

        return len(re.sub(r"\[/?.*?\]", "", self.text))


if __name__ == "__main__":
    app()
