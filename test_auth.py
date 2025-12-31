import requests

def test_login(username, password):
    url = "http://127.0.0.1:8000/api-token-auth/"
    data = {"username": username, "password": password}
    try:
        response = requests.post(url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        test_login(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python test_auth.py <username> <password>")
