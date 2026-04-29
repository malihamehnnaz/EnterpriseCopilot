import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

endpoint = os.getenv(
    "AZURE_AI_MISTRAL_ENDPOINT",
    "https://aaaadmin1347-resource001.services.ai.azure.com/openai/v1/",
)
deployment_name = os.getenv("AZURE_AI_MISTRAL_DEPLOYMENT", "Mistral-Large-3")
api_key = os.getenv("AZURE_AI_API_KEY")

if not api_key:
    raise RuntimeError("Set AZURE_AI_API_KEY in the .env file before running test.py")

client = OpenAI(
    base_url=endpoint,
    api_key=api_key,
)

completion = client.chat.completions.create(
    model=deployment_name,
    messages=[
        {
            "role": "user",
            "content": "What is the capital of France?",
        }
    ],
)

print(completion.choices[0].message.content)