"""Test login endpoint directly"""
import requests
import json

url = "http://localhost:8000/api/auth/login"
params = {
    "username": "admin",
    "password": "admin123"
}

print(f"Testing: POST {url}")
print(f"Params: {params}")
print()

try:
    response = requests.post(url, params=params)
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print()
    
    if response.status_code == 200:
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
    else:
        print("Response Text:")
        print(response.text[:500])  # First 500 chars
        
except Exception as e:
    print(f"Error: {e}")
