# MCP Server for ReportPortal

An MCP (Model Context Protocol) server that exposes ReportPortal API operations as tools for AI assistants. Covers launches, test items, logs, dashboards, widgets, filters, projects, users, and integrations.

## Prerequisites

- Python 3.11+
- A running ReportPortal instance (5.x)
- An API token or username/password credentials

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

The server reads configuration from three sources (in priority order):

1. **Environment variables** (`RP_URL`, `RP_TOKEN`, `RP_PROJECT`, etc.)
2. **`.env` file** in the project root
3. **`config.yaml`** file

### Quick Start

Copy the example files and fill in your values:

```bash
cp .env.example .env
# Edit .env with your ReportPortal URL, token, and project
```

Or use a YAML config:

```bash
cp config.example.yaml config.yaml
# Edit config.yaml with your settings
```

### Environment Variables

| Variable | Description | Required |
|---|---|---|
| `RP_URL` | ReportPortal server URL | Yes |
| `RP_TOKEN` | API token (from Profile > API Keys) | Yes* |
| `RP_PROJECT` | Project name | Yes |
| `RP_USERNAME` | Username (alternative to token) | No* |
| `RP_PASSWORD` | Password (alternative to token) | No* |
| `RP_VERIFY_SSL` | Verify SSL certificates (default `true`) | No |

\* Either `RP_TOKEN` or both `RP_USERNAME` and `RP_PASSWORD` are required.

## Usage

### Run with stdio transport (for Cursor, Claude Desktop, etc.)

```bash
python main.py
```

### Run with a specific config file

```bash
python main.py /path/to/config.yaml
```

### Cursor MCP Configuration

Add to your `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "reportportal": {
      "command": "python",
      "args": ["/path/to/mcp-rp/main.py"],
      "env": {
        "RP_URL": "https://reportportal.example.com",
        "RP_TOKEN": "your-api-token",
        "RP_PROJECT": "my_project"
      }
    }
  }
}
```

## Available Tools

### Launches (10 tools)

| Tool | Description |
|---|---|
| `rp_list_launches` | List launches with filters (status, name, mode, pagination) |
| `rp_get_launch` | Get launch by numeric ID |
| `rp_get_launch_by_uuid` | Get launch by UUID |
| `rp_create_launch` | Start a new launch |
| `rp_finish_launch` | Finish a running launch |
| `rp_force_finish_launch` | Force-finish a stuck launch |
| `rp_update_launch` | Update launch metadata |
| `rp_delete_launch` | Delete a launch |
| `rp_merge_launches` | Merge multiple launches |
| `rp_compare_launches` | Compare launch statistics |

### Test Items (11 tools)

| Tool | Description |
|---|---|
| `rp_list_test_items` | List test items with filters |
| `rp_get_test_item` | Get test item by ID |
| `rp_get_test_item_by_uuid` | Get test item by UUID |
| `rp_create_test_item` | Create a suite, test, or step |
| `rp_finish_test_item` | Finish a test item with status |
| `rp_update_test_item` | Update test item metadata |
| `rp_delete_test_item` | Delete a test item |
| `rp_get_test_item_history` | Get execution history |
| `rp_update_test_item_issues` | Bulk-update defect types |
| `rp_link_external_issue` | Link bug-tracker tickets |
| `rp_unlink_external_issue` | Unlink bug-tracker tickets |

### Logs (7 tools)

| Tool | Description |
|---|---|
| `rp_list_logs` | List logs with filters |
| `rp_get_log` | Get log by ID |
| `rp_get_log_by_uuid` | Get log by UUID |
| `rp_create_log` | Create a log entry |
| `rp_get_nested_step_logs` | Get logs for nested steps |
| `rp_search_logs` | Search for similar logs |
| `rp_delete_log` | Delete a log entry |

### Dashboards (7 tools)

| Tool | Description |
|---|---|
| `rp_list_dashboards` | List all dashboards |
| `rp_get_dashboard` | Get dashboard with widgets |
| `rp_create_dashboard` | Create a new dashboard |
| `rp_update_dashboard` | Update dashboard metadata |
| `rp_delete_dashboard` | Delete a dashboard |
| `rp_add_widget_to_dashboard` | Add a widget to a dashboard |
| `rp_remove_widget_from_dashboard` | Remove a widget |

### Widgets (5 tools)

| Tool | Description |
|---|---|
| `rp_list_widget_names` | List all widget names |
| `rp_get_widget` | Get widget details |
| `rp_create_widget` | Create a new widget |
| `rp_update_widget` | Update widget configuration |
| `rp_preview_widget` | Preview widget data |

### Filters (5 tools)

| Tool | Description |
|---|---|
| `rp_list_filters` | List all user filters |
| `rp_get_filter` | Get filter details |
| `rp_create_filter` | Create a new filter |
| `rp_update_filter` | Update a filter |
| `rp_delete_filter` | Delete a filter |

### Projects (8 tools)

| Tool | Description |
|---|---|
| `rp_list_projects` | List all projects |
| `rp_get_project` | Get project details |
| `rp_get_project_names` | Get lightweight project name list |
| `rp_create_project` | Create a new project |
| `rp_update_project` | Update project configuration |
| `rp_delete_project` | Delete a project |
| `rp_assign_user_to_project` | Assign a user with a role |
| `rp_unassign_user_from_project` | Remove a user |

### Users (6 tools)

| Tool | Description |
|---|---|
| `rp_get_current_user` | Get authenticated user profile |
| `rp_get_user` | Get user by login name |
| `rp_search_users` | Search users by name/email |
| `rp_list_api_keys` | List API keys for a user |
| `rp_create_api_key` | Create a new API key |
| `rp_delete_api_key` | Revoke an API key |

### Integrations (8 tools)

| Tool | Description |
|---|---|
| `rp_list_global_integrations` | List global integrations |
| `rp_list_project_integrations` | List project integrations |
| `rp_get_integration` | Get integration details |
| `rp_create_global_integration` | Create a global integration |
| `rp_create_project_integration` | Create a project integration |
| `rp_update_integration` | Update an integration |
| `rp_delete_integration` | Delete an integration |
| `rp_test_integration_connection` | Test integration connectivity |

## Architecture

```
main.py                  FastMCP server entry point
src/
  config/settings.py     Pydantic settings, YAML + env var loading
  clients/
    base.py              Abstract HTTP client interface
    reportportal.py      aiohttp client with OAuth, retries, rate limiting
  models/                Pydantic models for all RP entities
  services/              One service per domain (launch, test_item, log, ...)
  tools/                 MCP tool registrations per domain
  utils/
    logging.py           Structured logging (structlog)
    retry.py             Async retry with exponential backoff
```

## Development

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run linting
ruff check src/

# Run tests
pytest tests/
```
