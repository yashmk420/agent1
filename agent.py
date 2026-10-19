

import os
import json
from dotenv import load_dotenv
from openai import OpenAI

from github_files import list_files, read_file

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)

REPO = "yashmk420/agent-test-repo"

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
    }
]

available_functions = {
    "list_files": list_files,
    "read_file": read_file
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

            print(f"\nTool requested: {name}")
            print(f"Arguments: {arguments}")

            try:
                if name not in available_functions:
                    raise ValueError("Tool is not allowed")

                if arguments.get("repo") != REPO:
                    raise ValueError("Only the configured test repository is allowed")

                function = available_functions[name]
                result = function(**arguments)

                if isinstance(result, str):
                    tool_output = result
                else:
                    tool_output = json.dumps(result)

            except Exception as error:
                tool_output = f"Tool error: {error}"

            print(f"Tool result:\n{tool_output}")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_output
            })

    print("\nStopped: reached the 6-step tool-call limit.")


if __name__ == "__main__":
    ask_agent("What does this repository do?")
