#!/usr/bin/env python
"""Inspect the raw Kilocode API response to identify provider fields."""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from src.kilocode.client import KilocodeClient


async def main():
    async with KilocodeClient() as client:
        models = await client.list_models()

    print(f"Total models: {len(models)}")
    print("\n--- First model (full structure) ---")
    print(json.dumps(models[0], indent=2))
    print("\n--- Keys available in first 5 models ---")
    for i, m in enumerate(models[:5]):
        print(f"\nModel {i+1}: {m.get('id', 'n/a')}")
        print(f"  Keys: {list(m.keys())}")
        # Look for any provider-like field
        for key in m.keys():
            if any(x in key.lower() for x in ["provider", "owner", "vendor", "by", "source"]):
                print(f"  >>> {key}: {m[key]}")


asyncio.run(main())
