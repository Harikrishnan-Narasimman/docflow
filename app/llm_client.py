import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-5"
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def call_llm(system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )

    for block in response.content:
        if block.type == "text":
            return block.text.strip()
    raise ValueError("No text block found in Claude's response.")

def call_llm_json(system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> dict:
    """Same as call_llm, but expects a JSON object back and parses it.
    Strips markdown code fences if the model adds them despite instructions."""
    raw = call_llm(system_prompt, user_prompt, max_tokens=max_tokens)

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json\n", "", 1).replace("json\r\n", "", 1)
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model did not return valid JSON: {e}\nRaw output: {raw}")    