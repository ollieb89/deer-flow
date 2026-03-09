#!/usr/bin/env python3
"""Test script to verify Gemini model instantiation."""

import sys
from pathlib import Path

# Add the backend src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.app_config import get_app_config, reset_app_config
from models.factory import create_chat_model

def test_gemini_model():
    """Test that Gemini model can be instantiated."""
    try:
        # Reset config cache to ensure fresh load
        reset_app_config()
        
        # Load config (this will load .env and models.yaml)
        app_config = get_app_config()
        
        print(f"Loaded {len(app_config.models)} models")
        for model in app_config.models:
            print(f"  - {model.name}: {model.display_name} (use: {model.use})")
        
        # Test instantiating the gemini-2.5-flash model
        print("\nInstantiating gemini-2.5-flash model...")
        model = create_chat_model(name="gemini-2.5-flash")
        
        print(f"✓ Successfully created model instance: {type(model)}")
        print(f"  Model: {model}")
        
        # Get model attributes
        if hasattr(model, 'model'):
            print(f"  Underlying model: {model.model}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gemini_model()
    sys.exit(0 if success else 1)
