#!/usr/bin/env python
"""Test script to verify mise + uv venv integration works correctly.

This script validates that:
1. Python runs from the .venv virtual environment
2. VIRTUAL_ENV environment variable is set correctly
3. Key project dependencies can be imported from .venv

Run with: mise self-uv-test
"""
import sys
import os


def main():
    print("=" * 60)
    print("MISE + UV VENV INTEGRATION TEST")
    print("=" * 60)

    errors = []

    # 1. Check Python executable location
    print(f"\n1. Python executable: {sys.executable}")
    expected_venv = ".venv"
    if expected_venv in sys.executable:
        print("   ✅ Running from .venv (expected)")
    else:
        print("   ❌ NOT running from .venv - this is wrong!")
        errors.append("Python not running from .venv")

    # 2. Check sys.prefix (venv location)
    print(f"\n2. sys.prefix: {sys.prefix}")

    # 3. Check VIRTUAL_ENV env var
    venv = os.environ.get("VIRTUAL_ENV", "NOT SET")
    print(f"\n3. VIRTUAL_ENV: {venv}")
    if venv == "NOT SET":
        errors.append("VIRTUAL_ENV not set")

    # 4. Test key imports
    print("\n4. Testing imports:")
    imports_to_test = [
        ("temporalio", "Temporal workflow SDK"),
        ("anthropic", "Anthropic Claude SDK"),
        ("pydantic", "Pydantic data validation"),
        ("boto3", "AWS SDK"),
        ("requests", "HTTP library"),
    ]

    for module, desc in imports_to_test:
        try:
            mod = __import__(module)
            location = getattr(mod, "__file__", "built-in")
            print(f"   ✅ {module}: {desc}")
            print(f"      Location: {location}")
        except ImportError as e:
            print(f"   ❌ {module}: FAILED - {e}")
            errors.append(f"Import failed: {module}")

    # 5. Summary
    print("\n" + "=" * 60)
    if not errors:
        print("✅ ALL TESTS PASSED - mise + uv venv integration working!")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME TESTS FAILED:")
        for err in errors:
            print(f"   - {err}")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
