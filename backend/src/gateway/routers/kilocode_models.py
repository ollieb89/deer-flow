"""API routes for kilocode model discovery and management.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...db.connection import get_db_session
from ...db.models import KilocodeModel, KilocodeProvider, ModelSyncLog
from ...kilocode import dry_run_fetch, fetch_models

router = APIRouter(prefix="/api/kilocode", tags=["kilocode"])


# Request/Response models

class ProviderResponse(BaseModel):
    """Provider information response."""
    id: str
    name: str
    display_name: str | None
    description: str | None
    model_count: int


class ModelCapabilities(BaseModel):
    """Model capabilities."""
    vision: bool
    thinking: bool
    tool_calling: bool
    streaming: bool


class ModelPricing(BaseModel):
    """Model pricing information."""
    prompt: str | None
    completion: str | None


class ModelResponse(BaseModel):
    """Model information response."""
    id: str
    model_id: str
    name: str
    provider: ProviderResponse
    capabilities: ModelCapabilities
    context_length: int | None
    max_output_tokens: int | None
    pricing: ModelPricing | None
    is_active: bool
    is_featured: bool
    last_synced_at: str
    metadata: dict[str, Any] | None = None


class ModelsListResponse(BaseModel):
    """Response for listing models."""
    models: list[ModelResponse]
    total: int
    offset: int
    limit: int
    providers: list[ProviderResponse]


class StatsResponse(BaseModel):
    """System statistics for models and providers."""
    total_models: int
    active_models: int
    featured_models: int
    total_providers: int
    capabilities: dict[str, int]
    provider_distribution: dict[str, int]


class DryRunResponse(BaseModel):
    """Response for dry run operation."""
    total_models: int
    provider_count: int
    providers: list[dict[str, Any]]
    sample_models: list[dict[str, Any]]


class SyncRequest(BaseModel):
    """Request to sync models."""
    dry_run: bool = Field(default=False, description="If true, don't actually modify the database")


class SyncResponse(BaseModel):
    """Response for sync operation."""
    operation: str
    models_found: int
    models_added: int
    models_updated: int
    models_unchanged: int
    providers_created: int


class SyncLogResponse(BaseModel):
    """Response for sync log entries."""
    id: str
    operation: str
    status: str
    models_found: int | None
    models_added: int | None
    models_updated: int | None
    started_at: str
    completed_at: str | None
    error_message: str | None


# Dependency injection

def get_db():
    """Get database session dependency."""
    with get_db_session() as session:
        yield session


# Routes

@router.get(
    "/models",
    response_model=ModelsListResponse,
    summary="List Kilocode Models",
    description="Retrieve all models fetched from kilocode with filtering, search, and pagination.",
)
async def list_kilocode_models(
    provider: str | None = Query(None, description="Filter by provider name"),
    search: str | None = Query(None, description="Search in model names or IDs"),
    capabilities: list[str] | None = Query(None, description="Filter by capabilities (vision,thinking,tool_calling)"),
    is_featured: bool | None = Query(None, description="Filter by featured status"),
    sort_by: str = Query("name", description="Field to sort by (name, context_length, model_id)"),
    order: str = Query("asc", description="Sort order (asc, desc)"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> ModelsListResponse:
    """List all kilocode models with filtering and pagination.
    
    Args:
        provider: Filter by provider name
        search: Search string for model names/IDs
        capabilities: List of required capabilities
        is_featured: Filter by featured status
        sort_by: Field to sort by
        order: Sort order
        limit: Number of items to return
        offset: Number of items to skip
        db: Database session
        
    Returns:
        List of models, total count, and metadata.
    """
    # Build query
    query = select(KilocodeModel).where(KilocodeModel.is_active == True)
    
    if provider:
        query = query.join(KilocodeProvider).where(KilocodeProvider.name == provider)
    
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (KilocodeModel.name.ilike(search_filter)) | 
            (KilocodeModel.model_id.ilike(search_filter))
        )
    
    if is_featured is not None:
        query = query.where(KilocodeModel.is_featured == is_featured)
    
    if capabilities:
        if "vision" in capabilities:
            query = query.where(KilocodeModel.supports_vision == True)
        if "thinking" in capabilities:
            query = query.where(KilocodeModel.supports_thinking == True)
        if "tool_calling" in capabilities:
            query = query.where(KilocodeModel.supports_tool_calling == True)
    
    # Get total count before pagination
    from sqlalchemy import func
    total_query = select(func.count()).select_from(query.subquery())
    total = db.execute(total_query).scalar() or 0
    
    # Sorting
    allowed_sort_fields = ["name", "context_length", "model_id", "created_at", "last_synced_at"]
    if sort_by not in allowed_sort_fields:
        sort_by = "name"
    
    sort_attr = getattr(KilocodeModel, sort_by)
    if order.lower() == "desc":
        query = query.order_by(sort_attr.desc())
    else:
        query = query.order_by(sort_attr.asc())
    
    # Pagination
    query = query.limit(limit).offset(offset)
    
    # Execute query
    models = db.execute(query).scalars().all()
    
    # Get all providers with model counts (for the filter UI)
    providers_query = select(KilocodeProvider)
    providers = db.execute(providers_query).scalars().all()
    
    provider_responses = []
    for p in providers:
        model_count = len(p.models)
        if model_count > 0:
            provider_responses.append(ProviderResponse(
                id=p.id,
                name=p.name,
                display_name=p.display_name,
                description=p.description,
                model_count=model_count,
            ))
    
    # Sort providers by model count
    provider_responses.sort(key=lambda x: x.model_count, reverse=True)
    
    model_responses = []
    for m in models:
        model_responses.append(ModelResponse(
            id=m.id,
            model_id=m.model_id,
            name=m.name,
            provider=ProviderResponse(
                id=m.provider.id,
                name=m.provider.name,
                display_name=m.provider.display_name,
                description=m.provider.description,
                model_count=len(m.provider.models),
            ),
            capabilities=ModelCapabilities(
                vision=m.supports_vision,
                thinking=m.supports_thinking,
                tool_calling=m.supports_tool_calling,
                streaming=m.supports_streaming,
            ),
            context_length=m.context_length,
            max_output_tokens=m.max_output_tokens,
            pricing=ModelPricing(
                prompt=m.pricing_prompt,
                completion=m.pricing_completion,
            ) if m.pricing_prompt or m.pricing_completion else None,
            is_active=m.is_active,
            is_featured=m.is_featured,
            last_synced_at=m.last_synced_at.isoformat() if m.last_synced_at else "",
            metadata=m.model_metadata,
        ))
    
    return ModelsListResponse(
        models=model_responses,
        total=total,
        offset=offset,
        limit=limit,
        providers=provider_responses,
    )


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Get Model Statistics",
    description="Get higher-level statistics about models and providers.",
)
async def get_model_stats(
    db: Session = Depends(get_db),
) -> StatsResponse:
    """Retrieve statistics for models and providers."""
    total_models = db.execute(select(func.count(KilocodeModel.id))).scalar() or 0
    active_models = db.execute(select(func.count(KilocodeModel.id)).where(KilocodeModel.is_active == True)).scalar() or 0
    featured_models = db.execute(select(func.count(KilocodeModel.id)).where(KilocodeModel.is_featured == True)).scalar() or 0
    total_providers = db.execute(select(func.count(KilocodeProvider.id))).scalar() or 0
    
    # Capabilities stats
    vision_count = db.execute(select(func.count(KilocodeModel.id)).where(KilocodeModel.supports_vision == True)).scalar() or 0
    thinking_count = db.execute(select(func.count(KilocodeModel.id)).where(KilocodeModel.supports_thinking == True)).scalar() or 0
    tool_count = db.execute(select(func.count(KilocodeModel.id)).where(KilocodeModel.supports_tool_calling == True)).scalar() or 0
    
    # Provider distribution
    providers = db.execute(select(KilocodeProvider)).scalars().all()
    dist = {p.display_name or p.name: len(p.models) for p in providers}
    
    return StatsResponse(
        total_models=total_models,
        active_models=active_models,
        featured_models=featured_models,
        total_providers=total_providers,
        capabilities={
            "vision": vision_count,
            "thinking": thinking_count,
            "tool_calling": tool_count,
        },
        provider_distribution=dist,
    )


@router.get(
    "/models/{model_id:path}",
    response_model=ModelResponse,
    summary="Get Model Details",
    description="Get detailed information about a specific kilocode model. Supports path-based IDs with slashes.",
)
async def get_kilocode_model(
    model_id: str,
    db: Session = Depends(get_db),
) -> ModelResponse:
    """Get a specific kilocode model by ID.
    
    Args:
        model_id: The model ID (e.g., "anthropic/claude-sonnet-4.5")
        db: Database session
        
    Returns:
        Model details.
        
    Raises:
        HTTPException: 404 if model not found.
    """
    model = db.execute(
        select(KilocodeModel).where(KilocodeModel.model_id == model_id)
    ).scalar_one_or_none()
    
    if not model:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    
    return ModelResponse(
        id=model.id,
        model_id=model.model_id,
        name=model.name,
        provider=ProviderResponse(
            id=model.provider.id,
            name=model.provider.name,
            display_name=model.provider.display_name,
            description=model.provider.description,
            model_count=len(model.provider.models),
        ),
        capabilities=ModelCapabilities(
            vision=model.supports_vision,
            thinking=model.supports_thinking,
            tool_calling=model.supports_tool_calling,
            streaming=model.supports_streaming,
        ),
        context_length=model.context_length,
        max_output_tokens=model.max_output_tokens,
        pricing=ModelPricing(
            prompt=model.pricing_prompt,
            completion=model.pricing_completion,
        ) if model.pricing_prompt or model.pricing_completion else None,
        is_active=model.is_active,
        is_featured=model.is_featured,
        last_synced_at=model.last_synced_at.isoformat() if model.last_synced_at else "",
        metadata=model.model_metadata,
    )


@router.get(
    "/providers",
    response_model=list[ProviderResponse],
    summary="List Providers",
    description="List all model providers available through kilocode.",
)
async def list_providers(
    db: Session = Depends(get_db),
) -> list[ProviderResponse]:
    """List all kilocode providers.
    
    Returns:
        List of providers with model counts.
    """
    providers = db.execute(select(KilocodeProvider)).scalars().all()
    
    return [
        ProviderResponse(
            id=p.id,
            name=p.name,
            display_name=p.display_name,
            description=p.description,
            model_count=len(p.models),
        )
        for p in providers
    ]


@router.post(
    "/sync/dry-run",
    response_model=DryRunResponse,
    summary="Dry Run Model Sync",
    description="Preview what models would be synced without modifying the database.",
)
async def sync_dry_run() -> DryRunResponse:
    """Perform a dry run of model synchronization.
    
    Returns:
        Information about models that would be synced.
    """
    result = await dry_run_fetch()
    
    return DryRunResponse(
        total_models=result["total_models"],
        provider_count=result["provider_count"],
        providers=result["providers"],
        sample_models=result["sample_models"],
    )


@router.post(
    "/sync",
    response_model=SyncResponse,
    summary="Sync Models",
    description="Fetch and sync models from kilocode to the local database.",
)
async def sync_models(
    request: SyncRequest,
) -> SyncResponse:
    """Sync models from kilocode.
    
    Args:
        request: Sync configuration (dry_run option)
        
    Returns:
        Sync statistics.
    """
    result = await fetch_models(dry_run=request.dry_run)
    
    return SyncResponse(
        operation="dry_run" if request.dry_run else "sync",
        models_found=result.get("models_found", result.get("total_found", 0)),
        models_added=result.get("models_added", result.get("new_count", 0)),
        models_updated=result.get("models_updated", 0),
        models_unchanged=result.get("models_unchanged", 0),
        providers_created=result.get("providers_created", 0),
    )


@router.get(
    "/sync/logs",
    response_model=list[SyncLogResponse],
    summary="Get Sync Logs",
    description="Retrieve history of model synchronization operations.",
)
async def get_sync_logs(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[SyncLogResponse]:
    """Get recent sync logs.
    
    Args:
        limit: Maximum number of logs to return
        db: Database session
        
    Returns:
        List of sync log entries.
    """
    logs = db.execute(
        select(ModelSyncLog)
        .order_by(ModelSyncLog.started_at.desc())
        .limit(limit)
    ).scalars().all()
    
    return [
        SyncLogResponse(
            id=log.id,
            operation=log.operation,
            status=log.status,
            models_found=log.models_found,
            models_added=log.models_added,
            models_updated=log.models_updated,
            started_at=log.started_at.isoformat() if log.started_at else "",
            completed_at=log.completed_at.isoformat() if log.completed_at else None,
            error_message=log.error_message,
        )
        for log in logs
    ]


@router.post(
    "/models/{model_id:path}/toggle",
    response_model=ModelResponse,
    summary="Toggle Model Active State",
    description="Enable or disable a model in the local database.",
)
async def toggle_model(
    model_id: str,
    db: Session = Depends(get_db),
) -> ModelResponse:
    """Toggle the active state of a model.
    
    Args:
        model_id: The model ID
        db: Database session
        
    Returns:
        Updated model information.
        
    Raises:
        HTTPException: 404 if model not found.
    """
    model = db.execute(
        select(KilocodeModel).where(KilocodeModel.model_id == model_id)
    ).scalar_one_or_none()
    
    if not model:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    
    model.is_active = not model.is_active
    db.add(model)
    
    return ModelResponse(
        id=model.id,
        model_id=model.model_id,
        name=model.name,
        provider=ProviderResponse(
            id=model.provider.id,
            name=model.provider.name,
            display_name=model.provider.display_name,
            description=model.provider.description,
            model_count=len(model.provider.models),
        ),
        capabilities=ModelCapabilities(
            vision=model.supports_vision,
            thinking=model.supports_thinking,
            tool_calling=model.supports_tool_calling,
            streaming=model.supports_streaming,
        ),
        context_length=model.context_length,
        max_output_tokens=model.max_output_tokens,
        pricing=ModelPricing(
            prompt=model.pricing_prompt,
            completion=model.pricing_completion,
        ) if model.pricing_prompt or model.pricing_completion else None,
        is_active=model.is_active,
        is_featured=model.is_featured,
        last_synced_at=model.last_synced_at.isoformat() if model.last_synced_at else "",
    )
