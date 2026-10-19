import requests
import os
from dotenv import load_dotenv
load_dotenv()

token = os.getenv("GITHUB_TOKEN")
response = requests.get("https://api.github.com")

if not token:
    raise ValueError("GITHUB_TOKEN not found in .env")

url = "https://api.github.com/repos/yashmk420/agent-test-repo"

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json"
}

response = requests.get(url, headers=headers, timeout=15)

print("Status code:", response.status_code)

if response.status_code == 200:
    repo = response.json()
    print("Repository:", repo["name"])
    print("Private:", repo["private"])
else:
    print("Error:", response.json().get("message", "Unknown error"))