"""Database models for DeerFlow.

Includes models for storing kilocode provider and model metadata.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class KilocodeProvider(Base):
    """Represents a model provider (e.g., anthropic, openai, mistralai).
    
    Providers are the organizations that create AI models.
    """
    __tablename__ = "kilocode_providers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True, index=True)
    display_name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    website = Column(String(500), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    models = relationship("KilocodeModel", back_populates="provider", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<KilocodeProvider(name='{self.name}')>"


class KilocodeModel(Base):
    """Represents an AI model available through kilocode.
    
    Stores metadata about models fetched from the kilocode API.
    """
    __tablename__ = "kilocode_models"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Model identification
    model_id = Column(String(200), nullable=False, unique=True, index=True)
    """Full model ID as returned by kilocode API (e.g., 'anthropic/claude-sonnet-4.5')"""
    
    name = Column(String(200), nullable=False)
    """Human-readable model name"""
    
    # Provider relationship
    provider_id = Column(String(36), ForeignKey("kilocode_providers.id"), nullable=False, index=True)
    provider = relationship("KilocodeProvider", back_populates="models")
    
    # Model capabilities
    supports_vision = Column(Boolean, default=False, nullable=False, index=True)
    supports_thinking = Column(Boolean, default=False, nullable=False, index=True)
    supports_tool_calling = Column(Boolean, default=False, nullable=False, index=True)
    supports_streaming = Column(Boolean, default=True, nullable=False)
    
    # Context and pricing
    context_length = Column(Integer, nullable=True)
    max_output_tokens = Column(Integer, nullable=True)
    
    # Pricing (stored as strings to preserve precision, in USD per token)
    pricing_prompt = Column(String(50), nullable=True)
    pricing_completion = Column(String(50), nullable=True)
    
    # Additional metadata from kilocode
    model_metadata = Column("metadata", JSON, nullable=True)
    """Raw metadata from kilocode API for extensibility"""
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_featured = Column(Boolean, default=False, nullable=False, index=True)
    
    # Sync tracking
    last_synced_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f"<KilocodeModel(model_id='{self.model_id}')>"
    
    @property
    def provider_name(self) -> str:
        """Extract provider name from model_id."""
        return self.model_id.split("/")[0] if "/" in self.model_id else "unknown"
    
    @property
    def short_name(self) -> str:
        """Extract short model name from model_id."""
        return self.model_id.split("/")[-1] if "/" in self.model_id else self.model_id
    
    def to_dict(self) -> dict:
        """Convert model to dictionary representation."""
        return {
            "id": self.id,
            "model_id": self.model_id,
            "name": self.name,
            "provider": {
                "id": self.provider.id,
                "name": self.provider.name,
                "display_name": self.provider.display_name,
            } if self.provider else None,
            "capabilities": {
                "vision": self.supports_vision,
                "thinking": self.supports_thinking,
                "tool_calling": self.supports_tool_calling,
                "streaming": self.supports_streaming,
            },
            "context_length": self.context_length,
            "max_output_tokens": self.max_output_tokens,
            "pricing": {
                "prompt": self.pricing_prompt,
                "completion": self.pricing_completion,
            } if self.pricing_prompt or self.pricing_completion else None,
            "is_active": self.is_active,
            "is_featured": self.is_featured,
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
            "metadata": self.model_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ModelSyncLog(Base):
    """Log of model synchronization operations."""
    
    __tablename__ = "model_sync_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Sync operation details
    operation = Column(String(50), nullable=False)  # 'fetch', 'dry_run', 'sync'
    status = Column(String(50), nullable=False)  # 'started', 'completed', 'failed'
    
    # Results
    models_found = Column(Integer, nullable=True)
    models_added = Column(Integer, nullable=True)
    models_updated = Column(Integer, nullable=True)
    models_unchanged = Column(Integer, nullable=True)
    
    # Error information
    error_message = Column(Text, nullable=True)
    
    # Raw response data (for dry runs)
    raw_data = Column(JSON, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<ModelSyncLog(operation='{self.operation}', status='{self.status}')>"
