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

##CREATE BRANCH

def create_branch(repo, new_branch, from_branch="main"):
    token = os.getenv("GITHUB_TOKEN")

    headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json"
    }
 
    base_url = f"https://api.github.com/repos/{repo}/git/ref/heads/{from_branch}"

    response = requests.get(base_url, headers=headers)


    if response.status_code != 200:

     raise RuntimeError(
        f"Could not find base branch: {response.status_code} {response.text}"
    )

    base_sha = response.json()["object"]["sha"]

    create_url = f"https://api.github.com/repos/{repo}/git/refs"

    payload = {
    "ref": f"refs/heads/{new_branch}",
    "sha": base_sha
    }
    
    response = requests.post(create_url, headers=headers, json=payload)

    if response.status_code == 422:
     error_data = response.json()

     if error_data.get("message") == "Reference already exists":
        return {
            "already_exists": True,
            "ref": f"refs/heads/{new_branch}"
        }

     raise RuntimeError(
        f"Branch creation rejected by GitHub: {response.text}"
    )
     
     

    if response.status_code == 401:
     raise RuntimeError("GitHub token is invalid or expired.")

    if response.status_code == 403:
     raise RuntimeError(
        "GitHub denied branch creation. Check token permissions."
    )

    if response.status_code != 201:
     raise RuntimeError(
        f"Could not create branch: {response.status_code} {response.text}"
    )



    
    return response.json()

def apply_change(repo, path, new_content, sha, branch):


    if branch == "main":
        raise ValueError("Direct writes to main are not allowed.")
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

    

    
    encoded_content = base64.b64encode(
        new_content.encode("utf-8")
    ).decode("utf-8")

    # tell gitHub what to write and which version to update
    payload = {
        "message": f"Update {path} using AI agent",
        "content": encoded_content,
        "sha": sha,
        "branch": branch
    }

    # PUT requests an update to the file on GitHub.
    response = requests.put(url, headers=headers, json=payload)

    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"Could not update file: {response.status_code} {response.text}"
        )

    return response.json()


def write_file(repo, path, new_content):

    if repo!= "yashmk420/agent-test-repo":

        return "Error: only the configured test repo is allowed"
    
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



    if approval.strip().lower() != "yes":
        
      return "user rejected"

    branch = "agent/day19-readme-fix"

    
    try:
     branch_result = create_branch(repo, branch)
    except RuntimeError as error:
     return f"Could not create branch: {error}"

    if branch_result.get("already_exists"):
     return (
        f"Branch '{branch}' already exists. No file was changed. "
        "Choose a new branch name and try again."
    ) 

    try:
        apply_change(repo, path, new_content, sha, branch)
    except RuntimeError as error:
        return f"Could not apply change: {error}"

    return {
    "status": "success",
    "branch": branch,
    "path": path,
    "diff": diff_text
}



def open_pull_request(repo, head_branch, base="main", title="", body=""):
    url = f"https://api.github.com/repos/{repo}/pulls"

    headers = {
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github+json"
    }

    payload = {
        "title": title,
        "body": body,
        "head": head_branch,
        "base": base
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        return response.json()


    if response.status_code == 422:
     error_data = response.json()
     message = error_data.get("message", "")

     if "No commits between" in response.text:
        return {"error": "No changes between branches."}

     if "A pull request already exists" in response.text:
        return {"error": "A pull request already exists for these branches."}

     raise RuntimeError(
        f"GitHub rejected the pull request: {message}"
    )

    if response.status_code == 401:
     raise RuntimeError("GitHub token is invalid or expired.")

    if response.status_code == 403:
     raise RuntimeError(
        f"GitHub denied the request. {response.text}."
    )


    raise RuntimeError(
        f"Could not open pull request: {response.status_code} {response.text}"
    )




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

    result = create_branch(
    "yashmk420/agent-test-repo",
    "agent/day18-test"
    )

    print(result["ref"])
    print(result["object"]["sha"])
