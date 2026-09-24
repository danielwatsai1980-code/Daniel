import os
from openai import OpenAI

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key="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_",
)

completion = client.chat.completions.create(
    model="openai/gpt-oss-20b:groq",
    messages=[
        {
            "role": "user",
            "content": "write a story about a cat who learns to play the piano"
        }
    ],
)

print(completion.choices[0].message)