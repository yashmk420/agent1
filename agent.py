

import os
import json
from dotenv import load_dotenv
from openai import OpenAI

from github_files import list_files, read_file, write_file, open_pull_request
import logging


logging.basicConfig(
    filename="agent.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
load_dotenv()


api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)

REPO = "yashmk420/agent-test-repo"



def generate_pr_details(diff_text):
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You write concise GitHub pull request titles "
                    "and descriptions based only on the provided diff. "
                    "Return valid JSON with exactly two keys: "
                    "'title' and 'body'. Do not invent changes."
                )
            },
            {
                "role": "user",
                "content": f"Write PR details for this diff:\n\n{diff_text}"
            }
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)



tools = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and folders at a path in the test repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {
                        "type": "string",
                        "description": "Repository in owner/name format."
                    },
                    "path": {
                        "type": "string",
                        "description": "Folder path. Use an empty string for the root."
                    }
                },
                "required": ["repo", "path"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the text of a file in the test repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {
                        "type": "string",
                        "description": "Repository in owner/name format."
                    },
                    "path": {
                        "type": "string",
                        "description": "Path to the file."
                    }
                },
                "required": ["repo", "path"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": (
            "Propose new content for a file in the GitHub repository. "
            "The user must approve the diff before any changes are applied."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "Repository in owner/repo format."
                },
                "path": {
                    "type": "string",
                    "description": "Path of the file to update."
                },
                "new_content": {
                    "type": "string",
                    "description": "The complete proposed content of the file."
                }
            },
            "required": ["repo", "path", "new_content"],
            "additionalProperties": False
        },
        "strict": True
    }
} 


]

available_functions = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file
}


def ask_agent(question):
    messages = [
        {
            "role": "system",
            "content": (
                f"You are a code assistant inspecting {REPO}. "
                "Use the available tools to inspect actual repository "
                "contents before answering questions about the code. "
                "Do not invent file contents."
            )
        },
        {
            "role": "user",
            "content": question
        }
    ]

    successful_writes = 0
    total_tool_calls = 0

    for step in range(6):
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message

        if not message.tool_calls:
            print("\nFinal answer:")
            print(message.content)
            return

        messages.append(message)

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            logging.info(
                "Tool requested: %s | Repo: %s | Path: %s",
                name,
                arguments.get("repo", "<missing>"),
                arguments.get("path", "<missing>")
            )
            print(f"\nTool requested: {name}")
            print(f"Arguments: {arguments}")

            try:
                if total_tool_calls >=6:
                    raise ValueError("Blocked: max of 6 tool calls per run")
                total_tool_calls += 1
                if name not in available_functions:
                    raise ValueError("Tool is not allowed")

                if name == "write_file" and successful_writes >= 2:
                    raise ValueError("Blocked: maximum of 2 successful file writes per run.")
                
                if arguments.get("repo") != REPO:
                    raise ValueError("Only the configured test repository is allowed")

                
                function = available_functions[name]
                result = function(**arguments)

                if name == "write_file" and isinstance(result, dict):
                    if result.get("status") == "success":
                        successful_writes += 1

                if name == "write_file" and isinstance(result, dict):
                    if result.get("status") == "success":
                        details = generate_pr_details(result["diff"])

                        if approve_pr_details(details):
                            pr = open_pull_request(
                                repo=REPO,
                                head_branch=result["branch"],
                                base="main",
                                title=details["title"],
                                body=details["body"]
                            )
                            tool_output = f"Pull request opened: {pr['html_url']}"
                        else:
                            tool_output = (
                                f"Change committed to branch {result['branch']}, "
                                "but you declined to open the PR."
                            )
                    else:
                        tool_output = json.dumps(result)

                elif isinstance(result, str):
                    tool_output = result
                else:
                    tool_output = json.dumps(result)


                       
                       
            
            
            
            except Exception as error:
                tool_output = f"Tool error: {error}"

            if (
                 tool_output.startswith("Tool error:")
                 or tool_output.startswith("Blocked:")
                 or tool_output.startswith("Error:")
                 or tool_output == "user rejected"
            ):
                 logging.warning("Tool failed, rejected, or blocked: %s", name,
                                 tool_output)
            else:
                 logging.info("Tool completed: %s", name)


            print(f"Tool result:\n{tool_output}")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_output
            })

    print("\nStopped: reached the 6-step tool-call limit.")


## if __name__ == "__main__":

def approve_pr_details(details):
    print("\nProposed pull request")
    print("Title:", details["title"])
    print("\nDescription:")
    print(details["body"])

    approval = input("\nOpen this PR? Type yes or no: ")

    return approval.strip().lower() == "yes"



if __name__ == "__main__":
    try:
        ask_agent(
            "Read README.md in yashmk420/agent-test-repo. "
            "Inspect its actual contents and fix one genuine typo "
            "if one exists. Show me the diff and wait for my approval."
        )
    except Exception as error:
        print(f"Agent failed due to {error}")

   ## try: 
    ## ask_agent("Read README.md in yashmk420/agent-test-repo and add the sentence This project was inspected by my AI agent again for 69th time. at the end. Show me the diff and wait for my approval before applying it.")
   ## except Exception as error:
      ##  print(f"Agent failed due to {error}")