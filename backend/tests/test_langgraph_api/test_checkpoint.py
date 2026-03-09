"""Tests for langgraph_api checkpoint utilities."""

import os
import tempfile
from unittest.mock import patch

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import importlib.util
spec = importlib.util.spec_from_file_location(
    "langgraph_api", 
    os.path.join(os.path.dirname(__file__), "../../.langgraph_api/__init__.py")
)
langgraph_api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(langgraph_api)

get_checkpointer = langgraph_api.get_checkpointer


class TestGetCheckpointer:
    """Tests for get_checkpointer function."""

    def test_default_sqlite_checkpointer(self):
        """Test that default checkpointer is SQLite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            checkpointer = get_checkpointer("sqlite", db_path=db_path)
            assert isinstance(checkpointer, SqliteSaver)

    def test_memory_checkpointer(self):
        """Test creating memory checkpointer."""
        checkpointer = get_checkpointer("memory")
        assert isinstance(checkpointer, MemorySaver)

    def test_invalid_checkpointer_type(self):
        """Test that invalid checkpointer type raises error."""
        with pytest.raises(ValueError, match="Unsupported checkpointer type"):
            get_checkpointer("invalid")

    def test_sqlite_checkpointer_with_custom_path(self):
        """Test SQLite checkpointer with custom database path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "custom", "path", "checkpoints.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            checkpointer = get_checkpointer("sqlite", db_path=db_path)
            assert isinstance(checkpointer, SqliteSaver)
            assert os.path.exists(db_path)

    def test_env_var_db_path(self):
        """Test that LANGGRAPH_CHECKPOINT_DB env var is respected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "env.db")
            with patch.dict(os.environ, {"LANGGRAPH_CHECKPOINT_DB": db_path}):
                checkpointer = get_checkpointer("sqlite")
                assert isinstance(checkpointer, SqliteSaver)
