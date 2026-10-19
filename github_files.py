import os
import requests
from dotenv import load_dotenv

load_dotenv()

def list_files(repo, path=""):
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        raise ValueError("GITHUB_TOKEN not founder")

    url = f"https://api.github.com/repos/{repo}/contents/{path}"


    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.get(url, headers=headers, timeout=15)


    if response.status_code != 200:
        message = response.json().get("message", "Unknown error")
        raise RuntimeError(
            f"GitHub API error {response.status_code}: {message}"
        )

    items = response.json()

    return [
        {
            "name": item["name"],
            "type": item["type"]
        }
        for item in items
    ]


    
if __name__ == "__main__":
    try:
        files = list_files("yashmk420/agent-test-rep", "src")

        for item in files:
            print(f'{item["name"]} — {item["type"]}')

    except (ValueError, RuntimeError, requests.RequestException) as error:
        print(f"Could not list repository files: {error}")

