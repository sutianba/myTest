import requests
import json

url = "http://localhost:5000/api/register"
headers = {
    "Content-Type": "application/json"
}
data = {
    "username": "completely_new_user_123",
    "email": "completely_new_user_123@example.com",
    "password": "123456"
}

try:
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
