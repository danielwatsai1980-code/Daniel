import json
import os
import requests

MODEL = "meta-llama/Llama-3.3-70B-Instruct"
API_URL = "https://router.huggingface.co/v1/chat/completions"

HF_TOKEN = os.getenv("HF_TOKEN", "_")


def load_headlines_from_file(file_path):
    """Loads JSON data from a local file path."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze_sentiment(data):
    titles_list = [item["title"] for item in data]

    prompt_content = (
        "Analyze the sentiment of the following news headlines.\n"
        "Return ONLY a valid JSON array of objects. Each object must contain:\n"
        "- 'headline': exact headline text\n"
        "- 'sentiment': 'POSITIVE', 'NEGATIVE', or 'NEUTRAL'\n"
        "- 'confidence': float between 0.0 and 1.0\n"
        "- 'reason': brief explanation (1 sentence)\n\n"
        f"Headlines:\n{json.dumps(titles_list, indent=2)}"
    )

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a professional threat-intelligence sentiment analysis system. Respond exclusively with structured JSON.",
            },
            {"role": "user", "content": prompt_content},
        ],
        "temperature": 0.1,
        "max_tokens": 1500,
    }

    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )

    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]

    # Sanitize markdown code block formatting if returned by the LLM
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    return json.loads(content)


if __name__ == "__main__":
    # Path to your input headlines JSON file
    input_file = "headlines.json"
    output_file = "sentiment_results.json"

    if os.path.exists(input_file):
        print(f"Loading headlines from {input_file}...")
        headlines_data = load_headlines_from_file("./headlines.json")

        print("Analyzing sentiment via Hugging Face Router API...")
        results = analyze_sentiment(headlines_data)

        # Save results back to a file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        print(f"Analysis complete! Results saved to {output_file}")
    else:
        print(f"Error: {input_file} was not found in the current folder.")