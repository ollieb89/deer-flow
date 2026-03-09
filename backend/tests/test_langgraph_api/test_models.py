"""Tests for langgraph_api model utilities."""

import os
from unittest.mock import patch

import pytest
from langchain_openai import ChatOpenAI

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from dotenv import load_dotenv
load_dotenv()

# Import from the .langgraph_api package
# Note: Since the package name starts with a dot, we import it indirectly
# through the sys.path manipulation above
import importlib.util
spec = importlib.util.spec_from_file_location(
    "langgraph_api", 
    os.path.join(os.path.dirname(__file__), "../../.langgraph_api/__init__.py")
)
langgraph_api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(langgraph_api)

create_kilo_chat_model = langgraph_api.create_kilo_chat_model
create_kilo_model_from_config = langgraph_api.utils.models.create_kilo_model_from_config


class TestCreateKiloChatModel:
    """Tests for create_kilo_chat_model function."""

    def test_raises_error_without_api_key(self):
        """Test that function raises error when no API key is provided."""
        # Ensure no env var is set
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="No API key provided"):
                create_kilo_chat_model()

    def test_uses_provided_api_key(self):
        """Test that function uses explicitly provided API key."""
        with patch.dict(os.environ, {}, clear=True):
            model = create_kilo_chat_model(api_key="test-key")
            assert isinstance(model, ChatOpenAI)

    def test_uses_env_var_api_key(self):
        """Test that function reads API key from environment variable."""
        with patch.dict(os.environ, {"KILO_API_KEY": "env-key"}, clear=True):
            model = create_kilo_chat_model()
            assert isinstance(model, ChatOpenAI)

    def test_default_base_url(self):
        """Test that default base URL is set correctly."""
        with patch.dict(os.environ, {"KILO_API_KEY": "test-key"}, clear=True):
            model = create_kilo_chat_model()
            # ChatOpenAI stores base_url in openai_api_base
            assert "kilo.ai" in str(model.openai_api_base)

    def test_custom_base_url(self):
        """Test that custom base URL is respected."""
        with patch.dict(os.environ, {"KILO_API_KEY": "test-key"}, clear=True):
            model = create_kilo_chat_model(base_url="https://custom.kilo.ai/gateway")
            assert model.openai_api_base == "https://custom.kilo.ai/gateway"

    def test_default_model(self):
        """Test that default model is set correctly."""
        with patch.dict(os.environ, {"KILO_API_KEY": "test-key"}, clear=True):
            model = create_kilo_chat_model()
            assert "claude" in model.model_name.lower()

    def test_custom_model(self):
        """Test that custom model is respected."""
        with patch.dict(os.environ, {"KILO_API_KEY": "test-key"}, clear=True):
            model = create_kilo_chat_model(model="openai/gpt-4o")
            assert model.model_name == "openai/gpt-4o"

    def test_temperature_parameter(self):
        """Test that temperature parameter is passed correctly."""
        with patch.dict(os.environ, {"KILO_API_KEY": "test-key"}, clear=True):
            model = create_kilo_chat_model(temperature=0.5)
            assert model.temperature == 0.5

    def test_max_tokens_parameter(self):
        """Test that max_tokens parameter is passed correctly."""
        with patch.dict(os.environ, {"KILO_API_KEY": "test-key"}, clear=True):
            model = create_kilo_chat_model(max_tokens=1000)
            assert model.max_tokens == 1000


class TestCreateKiloModelFromConfig:
    """Tests for create_kilo_model_from_config function."""

    def test_basic_config(self):
        """Test creating model from basic config."""
        with patch.dict(os.environ, {}, clear=True):
            config = {
                "model": "openai/gpt-4o",
                "temperature": 0.5,
                "api_key": "config-key",
            }
            model = create_kilo_model_from_config(config)
            assert isinstance(model, ChatOpenAI)
            assert model.model_name == "openai/gpt-4o"
            assert model.temperature == 0.5

    def test_config_with_env_fallback(self):
        """Test that config falls back to environment variables."""
        with patch.dict(os.environ, {"KILO_API_KEY": "env-key"}, clear=True):
            config = {"model": "anthropic/claude-sonnet-4.5"}
            model = create_kilo_model_from_config(config)
            assert isinstance(model, ChatOpenAI)
