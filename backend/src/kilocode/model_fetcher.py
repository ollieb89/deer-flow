"""Model fetching and synchronization utilities.

Provides functions to fetch models from kilocode and sync them to the local database.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from dotenv import load_dotenv, find_dotenv

from ..db.connection import get_db_session, init_db
from ..db.models import KilocodeModel, KilocodeProvider, ModelSyncLog
from .client import KilocodeClient

logger = logging.getLogger(__name__)


class ModelFetcher:
    """Fetches and synchronizes models from kilocode to the local database.
    
    Example:
        >>> fetcher = ModelFetcher()
        >>> 
        >>> # Dry run - see what would be synced
        >>> result = await fetcher.dry_run()
        >>> print(f"Would add {result['models_added']} new models")
        >>>
        >>> # Actually sync
        >>> result = await fetcher.sync()
        >>> print(f"Added {result['models_added']}, updated {result['models_updated']}")
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        """Initialize the model fetcher.
        
        Args:
            api_key: kilocode API key. If None, reads from KILO_API_KEY env var.
            base_url: Base URL for the kilocode API.
        """
        self.api_key = api_key
        self.base_url = base_url
    
    async def dry_run(self) -> dict[str, Any]:
        """Perform a dry run to see what models would be synced.
        
        Returns:
            Dictionary with metadata about the models that would be synced,
            including sample models and provider statistics.
        """
        logger.info("Starting dry run of model fetch...")
        
        async with KilocodeClient(self.api_key, self.base_url) as client:
            # Fetch models from kilocode
            models = await client.list_models()
            
            # Group by provider
            providers = {}
            for model in models:
                provider_name = self._extract_provider_name(model)
                if provider_name not in providers:
                    providers[provider_name] = {
                        "name": provider_name,
                        "display_name": self._format_provider_name(provider_name),
                        "models": [],
                    }
                providers[provider_name]["models"].append({
                    "model_id": model.get("id"),
                    "name": model.get("name", model.get("id")),
                    "context_length": model.get("context_length"),
                    "pricing": model.get("pricing"),
                })
            
            result = {
                "operation": "dry_run",
                "total_models": len(models),
                "providers": list(providers.values()),
                "provider_count": len(providers),
                "sample_models": models[:5] if models else [],
                "raw_data": models[:20],  # Include first 20 for inspection
            }
            
            logger.info(
                "Dry run complete: %d models from %d providers",
                result["total_models"],
                result["provider_count"]
            )
            
            return result
    
    async def sync(self, dry_run: bool = False) -> dict[str, Any]:
        """Sync models from kilocode to the local database.
        
        Args:
            dry_run: If True, don't actually modify the database.
            
        Returns:
            Dictionary with sync statistics.
        """
        operation = "dry_run" if dry_run else "sync"
        logger.info("Starting %s operation...", operation)
        
        # Ensure tables exist (no-op if already created)
        init_db()
        
        # Create sync log
        sync_log = ModelSyncLog(
            operation=operation,
            status="started",
        )
        
        if not dry_run:
            with get_db_session() as session:
                session.add(sync_log)
        
        try:
            async with KilocodeClient(self.api_key, self.base_url) as client:
                # Fetch models from kilocode
                models_data = await client.list_models()
                
                if dry_run:
                    return await self._dry_run_sync(models_data)
                
                return await self._perform_sync(models_data, sync_log)
                
        except Exception as e:
            logger.exception("Model sync failed")
            
            if not dry_run:
                with get_db_session() as session:
                    sync_log.status = "failed"
                    sync_log.error_message = str(e)
                    sync_log.completed_at = datetime.now(timezone.utc)
                    session.add(sync_log)
            
            raise
    
    async def _dry_run_sync(self, models_data: list[dict]) -> dict[str, Any]:
        """Perform a dry run analysis without database modifications."""
        provider_stats = {}
        new_models = []
        existing_models = []
        
        # Get existing models from database
        with get_db_session() as session:
            existing_ids = {
                row[0] for row in 
                session.execute(select(KilocodeModel.model_id)).all()
            }
        
        for model_data in models_data:
            model_id = model_data.get("id")
            provider_name = self._extract_provider_name(model_data)
            
            # Track provider stats
            if provider_name not in provider_stats:
                provider_stats[provider_name] = {
                    "total": 0,
                    "new": 0,
                    "existing": 0,
                }
            
            ps = provider_stats[provider_name]
            ps["total"] += 1
            
            if model_id in existing_ids:
                existing_models.append(model_id)
                ps["existing"] += 1
            else:
                new_models.append(model_id)
                ps["new"] += 1
        
        return {
            "total_found": len(models_data),
            "new_count": len(new_models),
            "existing_count": len(existing_models),
            "providers": provider_stats,
            "new_models": new_models,
            "existing_models": existing_models,
        }

    async def _perform_sync(
        self,
        models_data: list[dict],
        sync_log: ModelSyncLog,
    ) -> dict[str, Any]:
        """Perform the actual database synchronization."""
        # Use flat stats to avoid nested dict type inference issues
        models_found = len(models_data)
        models_added = 0
        models_updated = 0
        providers_created = 0
        cap_vision = 0
        cap_thinking = 0
        cap_tool_calling = 0
        
        with get_db_session() as session:
            # 1. Get or create providers (batch approach)
            provider_names = {self._extract_provider_name(m) for m in models_data}
            existing_providers = {
                p.name: p for p in 
                session.execute(select(KilocodeProvider).where(KilocodeProvider.name.in_(provider_names))).scalars().all()
            }
            
            providers_cache = existing_providers.copy()
            for name in provider_names:
                if name not in providers_cache:
                    provider = KilocodeProvider(
                        name=name,
                        display_name=self._format_provider_name(name),
                    )
                    session.add(provider)
                    providers_cache[name] = provider
                    providers_created += 1
            
            # Flush to get IDs for new providers
            session.flush()
            
            # 2. Pre-fetch all existing models to avoid N+1 queries
            model_ids = [m.get("id") for m in models_data]
            existing_models = {
                m.model_id: m for m in 
                session.execute(select(KilocodeModel).where(KilocodeModel.model_id.in_(model_ids))).scalars().all()
            }
            
            # 3. Sync models
            for model_data in models_data:
                model_id = model_data.get("id")
                provider_name = self._extract_provider_name(model_data)
                
                existing = existing_models.get(model_id)
                
                if existing:
                    self._update_model_from_data(existing, model_data)
                    models_updated += 1
                    target_model = existing
                else:
                    new_model = KilocodeModel(
                        model_id=model_id,
                        name=model_data.get("name", model_id),
                        provider=providers_cache[provider_name],
                    )
                    self._update_model_from_data(new_model, model_data)
                    session.add(new_model)
                    models_added += 1
                    target_model = new_model
                
                # Track capability stats
                if target_model.supports_vision: cap_vision += 1
                if target_model.supports_thinking: cap_thinking += 1
                if target_model.supports_tool_calling: cap_tool_calling += 1
            
            # Update sync log
            sync_log.status = "completed"
            sync_log.models_found = models_found
            sync_log.models_added = models_added
            sync_log.models_updated = models_updated
            sync_log.completed_at = datetime.now(timezone.utc)
            session.add(sync_log)
        
        logger.info(
            "Sync complete: added=%d, updated=%d, providers_created=%d",
            models_added,
            models_updated,
            providers_created
        )
        
        return {
            "models_found": models_found,
            "models_added": models_added,
            "models_updated": models_updated,
            "providers_created": providers_created,
            "capabilities": {
                "vision": cap_vision,
                "thinking": cap_thinking,
                "tool_calling": cap_tool_calling,
            }
        }
    
    def _update_model_from_data(self, model: KilocodeModel, data: dict):
        """Update a model entity from API data.
        
        Field mapping based on Kilocode API response shape:
          - id: 'provider/model-name' (provider extracted from prefix)
          - name: human-readable name
          - context_length: max context window
          - top_provider.max_completion_tokens: max output tokens
          - supported_parameters: list of supported params (tools, reasoning, ...)
          - architecture.input_modalities: list (contains 'image' if vision capable)
          - pricing.prompt / pricing.completion: cost per token
        """
        model.name = data.get("name", data.get("id", model.model_id))
        model.context_length = data.get("context_length")
        
        # Max output tokens from top_provider block
        top_provider = data.get("top_provider", {})
        model.max_output_tokens = top_provider.get("max_completion_tokens")
        
        # Parse pricing
        pricing = data.get("pricing", {})
        if pricing:
            model.pricing_prompt = pricing.get("prompt")
            model.pricing_completion = pricing.get("completion")
        
        # Store raw metadata
        model.model_metadata = data
        model.last_synced_at = datetime.now(timezone.utc)
        
        # Infer capabilities from API data
        self._infer_capabilities(model, data)
    
    def _infer_capabilities(self, model: KilocodeModel, data: dict):
        """Infer model capabilities from Kilocode API response fields.
        
        Uses:
          - supported_parameters: e.g. ["tools", "reasoning", "max_tokens", ...]
          - architecture.input_modalities: e.g. ["text", "image"]
        """
        supported = set(data.get("supported_parameters") or [])
        arch = data.get("architecture") or {}
        input_modalities = set(arch.get("input_modalities") or [])
        
        # Vision: image in input modalities
        model.supports_vision = "image" in input_modalities
        
        # Thinking/reasoning: 'reasoning' or 'include_reasoning' in supported params
        model.supports_thinking = bool(
            {"reasoning", "include_reasoning"} & supported
        )
        
        # Tool calling: 'tools' in supported params
        model.supports_tool_calling = "tools" in supported
        
        # Streaming: assume true by default (all modern LLMs stream)
        # Override only if explicitly flagged off (no such field in current API)
        model.supports_streaming = True
    
    @staticmethod
    def _extract_provider_name(model_data: dict) -> str:
        """Extract provider name from model id (format: 'provider/model-name').
        
        Models without a '/' in the id are treated as 'kilo-custom'.
        """
        model_id = model_data.get("id", "")
        if "/" in model_id:
            return model_id.split("/")[0]
        return "kilo-custom"
    
    @staticmethod
    def _format_provider_name(name: str) -> str:
        """Convert provider slug to display name."""
        # Map common provider slugs to display names
        display_names = {
            "anthropic": "Anthropic",
            "openai": "OpenAI",
            "google": "Google",
            "mistralai": "Mistral AI",
            "meta-llama": "Meta",
            "microsoft": "Microsoft",
            "cohere": "Cohere",
            "ai21": "AI21 Labs",
            "amazon": "Amazon",
            "kilo-auto": "Kilo Auto (Routing)",
            "kilo-custom": "Kilo Custom",
            "moonshotai": "Moonshot AI",
            "minimax": "MiniMax",
            "deepseek": "DeepSeek",
            "qwen": "Qwen (Alibaba)",
            "x-ai": "xAI",
            "perplexity": "Perplexity",
            "nvidia": "NVIDIA",
        }
        
        return display_names.get(name.lower(), name.replace("-", " ").title())


# Convenience functions

async def dry_run_fetch(
    api_key: str | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Perform a dry run fetch to see available models.
    
    This is a convenience function that doesn't require database setup.
    
    Example:
        >>> result = await dry_run_fetch()
        >>> print(f"Found {result['total_models']} models")
        >>> for provider in result['providers']:
        ...     print(f"  {provider['name']}: {len(provider['models'])} models")
    """
    fetcher = ModelFetcher(api_key, base_url)
    return await fetcher.dry_run()


async def fetch_models(
    api_key: str | None = None,
    base_url: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Fetch models from kilocode and sync to database.
    
    Args:
        api_key: kilocode API key.
        base_url: kilocode base URL.
        dry_run: If True, don't modify the database.
        
    Returns:
        Sync statistics.
        
    Example:
        >>> # First, see what would be synced
        >>> preview = await fetch_models(dry_run=True)
        >>> print(f"Would add {preview['new_count']} models")
        >>>
        >>> # Then actually sync
        >>> result = await fetch_models()
        >>> print(f"Added {result['models_added']} models")
    """
    fetcher = ModelFetcher(api_key, base_url)
    return await fetcher.sync(dry_run=dry_run)


# CLI entry point
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch models from kilocode")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be synced without modifying database")
    parser.add_argument("--api-key", help="Kilocode API key (or set KILO_API_KEY env var)")
    parser.add_argument("--output", "-o", help="Output file for dry run results (JSON)")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON output")
    
    args = parser.parse_args()
    
    # Load environment variables from .env file
    load_dotenv(find_dotenv())
    
    async def main():
        fetcher = ModelFetcher(api_key=args.api_key)
        
        if args.dry_run:
            result = await fetcher.dry_run()
            
            print(f"\n{'='*60}")
            print(f"DRY RUN SUMMARY")
            print(f"{'='*60}")
            print(f"Total models found: {result['total_models']}")
            print(f"Providers: {result['provider_count']}")
            print(f"\nProviders breakdown:")
            for provider in sorted(result['providers'], key=lambda x: len(x['models']), reverse=True):
                print(f"  - {provider['display_name']:<25} {len(provider['models']):>3} models")
            
            # Save to file if requested
            if args.output:
                with open(args.output, 'w') as f:
                    if args.pretty:
                        json.dump(result, f, indent=2)
                    else:
                        json.dump(result, f)
                print(f"\nResults saved to: {args.output}")
        else:
            result = await fetcher.sync()
            
            print(f"\n{'='*60}")
            print(f"SYNC COMPLETE")
            print(f"{'='*60}")
            print(f"Models found:    {result['models_found']}")
            print(f"Models added:    {result['models_added']}")
            print(f"Models updated:  {result['models_updated']}")
            print(f"Providers newly created: {result.get('providers_created', 0)}")
            
            if "capabilities" in result:
                caps = result["capabilities"]
                print(f"\nCapability Distribution:")
                vision_pct = (caps['vision'] / result['models_found'] * 100) if result['models_found'] else 0
                thinking_pct = (caps['thinking'] / result['models_found'] * 100) if result['models_found'] else 0
                tools_pct = (caps['tool_calling'] / result['models_found'] * 100) if result['models_found'] else 0
                
                print(f"  Vision:       {caps['vision']:>3}  ({vision_pct:.0f}% of models)")
                print(f"  Tool calling: {caps['tool_calling']:>3}  ({tools_pct:.0f}% support functions)")
                print(f"  Thinking:     {caps['thinking']:>3}  ({thinking_pct:.0f}% support reasoning)")
            
            print(f"{'='*60}\n")
    
    asyncio.run(main())
