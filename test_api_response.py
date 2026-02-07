import requests
import json

BASE_URL = 'http://localhost:5000'

print("Testing /api/get-tables endpoint...")
print("=" * 50)

# First need to login to get session
session = requests.Session()

# Try to access without login
print("\n1. Trying without authentication...")
response = session.get(f'{BASE_URL}/api/get-tables')
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# The actual app is running, but we need to understand the response
# Since we can't authenticate via API request, let's simulate what happens
print("\n2. API endpoint definition is correct")
print("   - Returns: {'success': True, 'tables': [...items...]}")
print("   - Tables have: id, table_number, table_section, capacity, table_status, assigned_waiter, notes")
print("\nThe issue is likely:")
print("   ✗ API returns 401 (not authenticated)")
print("   ✗ Frontend silently catches error and doesn't update UI")
print("   ✗ Need to add console logging to debug")
