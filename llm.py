from openai import OpenAI
from dotenv import load_dotenv
import os
import time
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

## print("Key found:", api_key is not None)



def ask_llm(prompt):

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )

    stream = client.responses.create(
        input=prompt,
        model="openai/gpt-oss-20b",
        stream=True,
    )

    answer = ""

    for event in stream:
        if event.type == "response.output_text.delta":
            print(event.delta, end="", flush=True)
            time.sleep(0.01)
            answer += event.delta

    print()
    return answer
