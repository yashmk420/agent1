import os
import requests
import base64
import difflib
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


    

def read_file(repo, path, max_chars=12000):
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        raise ValueError("GITHUB_TOKEN not found in .env")

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

    data = response.json()

    if data.get("type") != "file":
        raise ValueError(f"{path} is not a file")

    encoded_content = data["content"]
    raw_bytes = base64.b64decode(encoded_content)
    text = raw_bytes.decode("utf-8")

    if len(text) > max_chars:
        text = text[:max_chars] + "\n...[truncated]"

    return text





def propose_change(repo, path, new_content):
    old_content = read_file(repo, path)

    diff = difflib.unified_diff(
        old_content.splitlines(),
        new_content.splitlines(),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        lineterm=""
    )

    diff_text = "\n".join(diff)

    print(diff_text if diff_text else "No changes proposed.")

    return diff_text


def get_file_data(repo, path):
    url = f"https://api.github.com/repos/{repo}/contents/{path}"

    token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise RuntimeError(
            f"Could not fetch file: {response.status_code} {response.text}"
        )

    data = response.json()

    content = base64.b64decode(data["content"]).decode("utf-8")
    sha = data["sha"]

    return content, sha

def apply_change(repo, path, new_content, sha):
    # Build the GitHub API URL for this file.
    url = f"https://api.github.com/repos/{repo}/contents/{path}"

    # Use the same authentication headers as your existing functions.
    token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    # Fetch the current file so we can get its SHA.
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise RuntimeError(
            f"Could not fetch file: {response.status_code} {response.text}"
        )

    

    # GitHub expects the new file contents in Base64.
    encoded_content = base64.b64encode(
        new_content.encode("utf-8")
    ).decode("utf-8")

    # Tell GitHub what to write and which version to update.
    payload = {
        "message": f"Update {path} using AI agent",
        "content": encoded_content,
        "sha": sha
    }

    # PUT requests an update to the file on GitHub.
    response = requests.put(url, headers=headers, json=payload)

    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"Could not update file: {response.status_code} {response.text}"
        )

    return response.json()


def write_file(repo, path, new_content):

    old_content, sha = get_file_data(repo, path)


    diff = difflib.unified_diff(
        old_content.splitlines(),
        new_content.splitlines(),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        lineterm=""
    )

    diff_text = "\n".join(diff)
    print(diff_text if diff_text else "No changes proposed.")

    if not diff_text:
        return "No changes needed"


    # Pause and ask the human to approve.
    approval = input("Apply this change? Type yes or no: ")

    if approval.strip().lower() == "yes":
        result = apply_change(repo, path, new_content, sha)
        return "Change applied successfully to GitHub."

    # Any response other than yes rejects the change.
    return "user rejected"





if __name__ == "__main__":
    try:
        files = list_files("yashmk420/agent-test-repo")

        for item in files:
            print(f'{item["name"]} — {item["type"]}')

    except (ValueError, RuntimeError, requests.RequestException) as error:
        print(f"Could not list repository files: {error}")


    print(read_file("yashmk420/agent-test-repo", "README.md"))

    old_content = read_file("yashmk420/agent-test-repo", "README.md")

    new_content = old_content + "\n\nThis is my first AI coding agent."

    propose_change(
    "yashmk420/agent-test-repo",
    "README.md",
     new_content
    )
