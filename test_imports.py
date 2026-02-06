#!/usr/bin/env python3
"""Test script to verify Flask app imports correctly"""

import sys
import os

print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")
print()

try:
    print("[TEST 1] Importing Flask...")
    from flask import Flask
    print("  ✓ Flask imported")
except ImportError as e:
    print(f"  ✗ Flask import failed: {e}")
    sys.exit(1)

try:
    print("[TEST 2] Importing Werkzeug...")
    from werkzeug.security import generate_password_hash, check_password_hash
    print("  ✓ Werkzeug imported")
except ImportError as e:
    print(f"  ✗ Werkzeug import failed: {e}")
    sys.exit(1)

try:
    print("[TEST 3] Importing app.py...")
    import app
    print(f"  ✓ app.py imported")
    print(f"  ✓ Database path: {app.DB_PATH}")
except Exception as e:
    print(f"  ✗ app.py import failed: {e}")
    sys.exit(1)

print()
print("[SUCCESS] All imports working correctly! ✓")

# Test password hashing
try:
    print()
    print("[TEST 4] Password hashing test...")
    test_password = "123456"
    hashed = generate_password_hash(test_password)
    verified = check_password_hash(hashed, test_password)
    print(f"  Original: {test_password}")
    print(f"  Hashed: {hashed[:40]}...")
    print(f"  Verified: {verified}")
    if verified:
        print("  ✓ Password hashing works!")
    else:
        print("  ✗ Password verification failed!")
except Exception as e:
    print(f"  ✗ Password test failed: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("ALL TESTS PASSED ✓")
print("=" * 60)
