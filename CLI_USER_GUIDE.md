# MTNA RDS CLI User Guide

The `mtnards` CLI provides a powerful, hierarchical interface for interacting with MTNA Rich Data Services (RDS) servers. It features an interactive shell-first design, making it easy to discover datasets, inspect metadata, and manage data resources.

## 1. Getting Started

### Installation
The tool is part of the `mtnards-toolkit`. You can run it directly using `uv`:
```bash
uv run mtnards
```

### Environment Variables
For the best experience, configure your RDS host and API key via environment variables:
```bash
export MTNA_RDS_HOST="https://rds.yourserver.net"
export MTNA_RDS_API_KEY="your-api-key"
```

### Starting the CLI
If credentials are set, simply running the command starts the **Interactive Shell**:
```bash
uv run mtnards
```
Otherwise, use options:
```bash
uv run mtnards --host "https://rds.yourserver.net" --api-key "secret"
```

---

## 2. Hierarchical Path Resolution

The CLI treats the RDS server like a virtual filesystem. You can navigate through **Catalogs**, **Data Products**, and **Variables** using a variety of path formats.

### Path Examples
- **Relative**: `catalog_id.product_id`
- **Absolute**: `.global_catalog` (starts with `.`)
- **Move Up**: `..` (returns to parent level)
- **Nested**: `cd mycat.myprod.myvar`

### Special Shortcuts
- **Property Access (`@`)**: Attach `@` and a property name to inspect specific metadata.
  - `show myproduct@label`
  - `show myvar@description`
- **Classification Shortcut (`$`)**: Use `$` to quickly list classification codes for a variable.
  - `ls myvar$` (shows codes for the variable)
  - `ls $` (while inside a variable, shows its classifications)

---

## 3. Interactive Shell Commands

The shell supports standard navigation and metadata management commands.

| Command | Usage | Description |
| :--- | :--- | :--- |
| `ls` | `ls [path] [--limit N] [--offset M] [--count]` | List contents. Displays total count and current page range. Use `--count` (or `-n`) for only the total number. |
| `cd` | `cd [path]` | Navigate into a catalog or data product. |
| `show` | `show [path][@property]` | Display detailed metadata for a resource. |
| `set` | `set <path@prop> [val] [--edit]` | Update a metadata property (with optional editor). |
| `variables` | `variables` | Shortcut to list all variables in the current product. |
| `classifications` | `classifications` | Shortcut to list all classifications in the current product. |
| `info` | `info` | Display basic information about the connected server. |
| `context` | `context` | Show current server, catalog, and product status. |
| `history` | `history` | View a list of recently executed commands. |
| `clear` | `clear` | Clear the terminal window. |
| `help` | `help` | Display context-sensitive list of available shell commands. |
| `debug` | `debug [on|off]` | Toggle visibility of underlying API call details. |
| `exit` | `exit` | Close the interactive shell session. |

---

## 4. Scripting & Automation

You can automate sequences of RDS commands by saving them in a `.rds` file and using the `run` command.

### Example Script (`check-metadata.rds`)
```bash
# This is a comment
connect "https://rds.highvaluedata.net"
ls .us-anes
show us-anes.anes1948@label
show us-anes.anes1948.VVERSION@description
exit
```

### Running a Script
```bash
uv run mtnards run check-metadata.rds
```

---

## 5. Tips & Best Practices

- **Resource Counts**: Use `ls --count` (or `ls -n`) to quickly check the size of a catalog or product without listing all items. Listing tables also show the total count in their title.
- **Pagination**: Use `--limit` with `ls` to handle large catalogs (e.g., `ls --limit 500`) and `--offset` to navigate pages.
- **Editor Support**: Use `set path@property --edit` to open your system's default editor (e.g., VS Code, Vim) for long descriptions.
- **Debug Mode**: Use `debug on` to see the actual API requests the tool is making. This is helpful for understanding the underlying RDS protocol.
- **Root Paths**: Paths starting with a dot (e.g., `.mycat`) always resolve relative to the server root, regardless of where you are.
- **Dot-Notation**: You don't always need `cd`. You can run `ls cat.prod` from anywhere in the shell.

---

> [!NOTE]
> All management commands like `stats`, `search`, and `export` are currently being finalized and will be fully integrated with existing RDS server endpoints in the next release.
