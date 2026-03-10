"""Test login API endpoint"""
import requests

# Test login endpoint (backend typically runs on port 8000)
url = "http://localhost:8000/api/auth/login"
params = {
    "username": "admin",
    "password": "admin123"
}

print(f"Testing login API: {url}")
print(f"Parameters: {params}")
print()

try:
    response = requests.post(url, params=params, timeout=5)
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
        print("\n[SUCCESS] Login works correctly!")
    else:
        print(f"Response text: {response.text}")
except requests.exceptions.ConnectionError:
    print("[ERROR] Cannot connect to backend server")
    print("Please make sure the backend is running:")
    print("  cd backend")
    print("  uvicorn app.main:app --reload --port 8000")
    print("\nOr check if it's running on a different port.")
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")
