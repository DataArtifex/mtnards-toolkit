# Agent-First CLI Specification

The `dartfx-mtnards` CLI is designed as a **shell-first, scriptable environment** optimized for both interactive use and automated agent interaction with MTNA RDS servers.

## Core Capabilities for Agents

### 1. Hierarchical Context Management
The CLI maintains a stateful context (Server > Catalog > Product) which reduces command length and complexity.
- Navigation via `cd [path]` and `ls [path]`.
- Path resolution supports dot-notation: `catalog.product.variable`.
- Absolute paths start with a slash or dot: `/my_catalog` or `.my_catalog`.
- Contextual defaults: If inside a product, `ls` shows variables.

### 2. High-Efficiency Resource Discovery
Agents should use shortcuts to minimize data transfer and parsing complexity:
- **Property Extraction (`@`)**: Query specific metadata without fetching the entire resource.
  - `show myproduct@label`
  - `show variable_id@description`
- **Classification Shortcuts (`$`)**: Quickly list category codes for categorical variables.
  - `ls variable_id$`
  - `ls $` (from within a variable context)

### 3. Scripted Execution (`run` command)
Agents can generate and execute `.rds` script files for batch operations.
- Support for sequential operations: `connect`, `cd`, `ls`, `show`, `export`, etc.
- Support for `#` comments to document agent intent within generated scripts.
- Scripts stop on the first failing command, providing predictable error handling.

### 4. Metadata Management
The CLI provides granular control over resource metadata:
- **`set` command**: Update any property using dot-notation or within context.
- **`--edit` flag**: Useful when an agent needs to hand off a long-form description to a human editor.
- **Multi-line support**: Quoted strings support multi-line text blocks.

## Command Reference for Scripting

| Command | Recommended Agent Usage |
| :--- | :--- |
| `ls` | Resource discovery with `--limit`/`--offset` to handle large catalogs and `--count` for quick profiling. |
| `show` | Fetch specific properties via `@` to maintain high token efficiency. Use `--codes` to peek at categorization. |
| `api` | Audit API request latency and status for observability. |
| `whoami` | Verify connection/context. |
| `debug` | Toggle underlying API call visibility. |
| `run` | Execute pre-generated logic batches. |
| `stats` | Initial profiling of catalogs and products. |
| `search` | Find resources by semantic match across the server. |
| `export` | Trigger server-side generation of Croissant or RDF documentation. |

---

> [!IMPORTANT]
> The CLI is the preferred interaction method for complex discovery tasks involving multiple levels of resource depth. When using the CLI via a subagent, always specify absolute paths (starting with `/` or `.`) to avoid context ambiguity. Use the `api` command to monitor performance if timeouts or high-latency responses are detected.
