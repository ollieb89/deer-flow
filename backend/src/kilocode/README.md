# Kilocode Model Discovery

A comprehensive model discovery and management system for integrating with the [kilocode AI Gateway](https://kilo.ai). This module provides automated model fetching, database storage, and a full-featured UI for browsing and managing available AI models.

## Overview

The kilocode Model Discovery system allows you to:

- **Fetch models** from kilocode's unified AI gateway API
- **Store model metadata** in a local database (SQLite by default)
- **Browse and filter** models by provider, capabilities, and search terms
- **Enable/disable** models for use in your application
- **Track sync history** with dry-run support

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   kilocode API  │────▶│  Model Fetcher  │────▶│   Database      │
│  (kilo.ai)      │     │  (client.py)    │     │   (SQLite/      │
│                 │     │                 │     │    Postgres)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   API Router    │
                       │  (FastAPI)      │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   React UI      │
                       │  (Settings)     │
                       └─────────────────┘
```

## Quick Start

### 1. Configuration

Set your kilocode API key:

```bash
export KILO_API_KEY="your-kilocode-api-key"
# Optional: custom base URL
# export KILO_BASE_URL="https://api.kilo.ai/api/gateway"
```

### 2. Database Setup

The database is automatically initialized on first run. Default location:
- SQLite: `./deerflow.db`

To customize:
```bash
export DATABASE_URL="sqlite:///custom/path.db"
# or for PostgreSQL:
# export DATABASE_URL="postgresql://user:pass@localhost/deerflow"
```

### 3. First Sync

#### Option A: Using the CLI

```bash
# Dry run to preview available models
python -m src.kilocode.model_fetcher --dry-run --pretty

# Actually sync to database
python -m src.kilocode.model_fetcher
```

#### Option B: Using the API

```bash
# Dry run
curl -X POST http://localhost:8001/api/kilocode/sync/dry-run

# Sync with database
curl -X POST http://localhost:8001/api/kilocode/sync \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}'
```

#### Option C: Using the UI

1. Open the web interface
2. Go to **Settings** → **Models**
3. Click **"Sync from Kilocode"**
4. Review the dry-run results
5. Click **"Sync to Database"**

## API Reference

### Models

#### List Models
```http
GET /api/kilocode/models?provider=anthropic&search=claude&capabilities=vision,thinking
```

Query Parameters:
- `provider` - Filter by provider name (e.g., "anthropic", "openai")
- `search` - Search in model names
- `capabilities` - Filter by capabilities: `vision`, `thinking`, `tool_calling`

Response:
```json
{
  "models": [
    {
      "id": "uuid",
      "model_id": "anthropic/claude-sonnet-4.5",
      "name": "Claude Sonnet 4.5",
      "provider": {
        "id": "uuid",
        "name": "anthropic",
        "display_name": "Anthropic",
        "model_count": 5
      },
      "capabilities": {
        "vision": true,
        "thinking": true,
        "tool_calling": true,
        "streaming": true
      },
      "context_length": 200000,
      "max_output_tokens": 8192,
      "pricing": {
        "prompt": "0.000003",
        "completion": "0.000015"
      },
      "is_active": true,
      "is_featured": false,
      "last_synced_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "providers": [...]
}
```

#### Get Model Details
```http
GET /api/kilocode/models/anthropic/claude-sonnet-4.5
```

#### Toggle Model Active State
```http
POST /api/kilocode/models/anthropic/claude-sonnet-4.5/toggle
```

### Providers

#### List Providers
```http
GET /api/kilocode/providers
```

Response:
```json
[
  {
    "id": "uuid",
    "name": "anthropic",
    "display_name": "Anthropic",
    "description": null,
    "model_count": 5
  }
]
```

### Sync Operations

#### Dry Run
Preview available models without modifying the database:

```http
POST /api/kilocode/sync/dry-run
```

Response:
```json
{
  "total_models": 150,
  "provider_count": 12,
  "providers": [
    {
      "name": "anthropic",
      "display_name": "Anthropic",
      "models": [...]
    }
  ],
  "sample_models": [...]
}
```

#### Sync Models
```http
POST /api/kilocode/sync
Content-Type: application/json

{"dry_run": false}
```

Response:
```json
{
  "operation": "sync",
  "models_found": 150,
  "models_added": 25,
  "models_updated": 10,
  "models_unchanged": 115,
  "providers_created": 2
}
```

#### Sync Logs
```http
GET /api/kilocode/sync/logs?limit=10
```

## Python API

### Using the Client

```python
import asyncio
from src.kilocode import KilocodeClient

async def main():
    async with KilocodeClient() as client:
        # List all models from kilocode
        models = await client.list_models()
        print(f"Found {len(models)} models")
        
        # List providers
        providers = await client.list_providers()
        for provider in providers:
            print(f"  - {provider['name']}")
        
        # Get specific model
        model = await client.get_model("anthropic/claude-sonnet-4.5")
        print(f"Context length: {model.get('context_length')}")

asyncio.run(main())
```

### Using the Model Fetcher

```python
import asyncio
from src.kilocode import ModelFetcher

async def main():
    fetcher = ModelFetcher()
    
    # Dry run
    dry_run_result = await fetcher.dry_run()
    print(f"Would sync {dry_run_result['total_models']} models")
    
    # Actual sync
    sync_result = await fetcher.sync(dry_run=False)
    print(f"Added: {sync_result['models_added']}")
    print(f"Updated: {sync_result['models_updated']}")

asyncio.run(main())
```

### Database Access

```python
from src.db import get_db_session
from src.db.models import KilocodeModel, KilocodeProvider

# Query models
with get_db_session() as session:
    # Get all active models
    active_models = session.query(KilocodeModel).filter_by(is_active=True).all()
    
    # Get models by provider
    anthropic_models = session.query(KilocodeModel).join(KilocodeProvider).filter(
        KilocodeProvider.name == "anthropic"
    ).all()
    
    # Get models with vision support
    vision_models = session.query(KilocodeModel).filter_by(supports_vision=True).all()
    
    for model in vision_models:
        print(f"{model.name}: {model.context_length} tokens")
```

## Frontend Usage

### React Components

The UI is integrated into the Settings dialog:

```tsx
import { ModelSettingsPage } from "@/components/workspace/settings/model-settings";

// Used in settings-dialog.tsx
<SettingsSection title="Models" description="Manage AI models">
  <ModelSettingsPage />
</SettingsSection>
```

### API Hooks

```tsx
import { 
  fetchKilocodeModels, 
  syncKilocodeModels, 
  dryRunSync 
} from "@/core/kilocode";

// Fetch models
const models = await fetchKilocodeModels({
  provider: "anthropic",
  search: "claude",
  capabilities: ["vision", "thinking"]
});

// Dry run
const preview = await dryRunSync();
console.log(`Found ${preview.total_models} models`);

// Sync
const result = await syncKilocodeModels(false);
console.log(`Added ${result.models_added} models`);
```

## Data Model

### KilocodeProvider

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `name` | String | Provider slug (e.g., "anthropic") |
| `display_name` | String | Human-readable name |
| `description` | Text | Provider description |
| `website` | String | Provider website URL |

### KilocodeModel

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `model_id` | String | Full model ID (e.g., "anthropic/claude-sonnet-4.5") |
| `name` | String | Display name |
| `provider_id` | UUID | Foreign key to provider |
| `supports_vision` | Boolean | Vision/image input support |
| `supports_thinking` | Boolean | Reasoning/thinking support |
| `supports_tool_calling` | Boolean | Function calling support |
| `supports_streaming` | Boolean | Streaming response support |
| `context_length` | Integer | Maximum context window |
| `max_output_tokens` | Integer | Maximum output tokens |
| `pricing_prompt` | String | Input token price (USD) |
| `pricing_completion` | String | Output token price (USD) |
| `metadata` | JSON | Raw API response data |
| `is_active` | Boolean | Enabled for use |
| `is_featured` | Boolean | Featured/promoted |
| `last_synced_at` | DateTime | Last sync timestamp |

## Supported Providers

Models from these providers are available through kilocode:

- **Anthropic** - Claude models (Sonnet, Opus, Haiku)
- **OpenAI** - GPT-4, GPT-4o, GPT-3.5
- **Google** - Gemini models
- **Mistral AI** - Mistral and Mixtral models
- **Meta** - Llama models
- **Microsoft** - Phi models
- **And more** - 100+ models from various providers

## Troubleshooting

### "No API key provided"
Set the `KILO_API_KEY` environment variable:
```bash
export KILO_API_KEY="your-api-key"
```

### "Failed to fetch models"
Check your network connection and API key validity:
```bash
curl -H "Authorization: Bearer $KILO_API_KEY" \
  https://api.kilo.ai/api/gateway/models
```

### Database locked (SQLite)
Ensure no other processes are accessing the database file.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KILO_API_KEY` | Required | Your kilocode API key |
| `KILO_BASE_URL` | `https://api.kilo.ai/api/gateway` | API base URL |
| `DATABASE_URL` | `sqlite:///./deerflow.db` | Database connection string |
| `LANGGRAPH_CHECKPOINT_DB` | - | Path for checkpoint database |
| `SQL_ECHO` | `false` | Log SQL queries (debug) |

## CLI Reference

```bash
python -m src.kilocode.model_fetcher [OPTIONS]

Options:
  --dry-run          Show what would be synced without modifying database
  --api-key TEXT     Kilocode API key (or set KILO_API_KEY env var)
  --output, -o FILE  Output file for dry run results (JSON)
  --pretty           Pretty print JSON output
  --help             Show help message
```

## Contributing

When adding new features:

1. Update the database models in `src/db/models.py`
2. Add API endpoints in `src/gateway/routers/kilocode_models.py`
3. Update the TypeScript types in `frontend/src/core/kilocode/types.ts`
4. Add frontend components as needed
5. Update this README

## See Also

- [Kilocode Documentation](https://kilo.ai/docs)
- [Kilocode Models](https://kilo.ai/docs/models)
- [API Reference](https://kilo.ai/docs/gateway/api-reference)
