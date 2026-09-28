import os
import requests
import re
from pathlib import Path

# Load environment variables from local .env if present
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if "=" in line_str and not line_str.startswith("#"):
                    k, v = line_str.split("=", 1)
                    if k.strip() == "OPENROUTER_API_KEY" and not os.environ.get("OPENROUTER_API_KEY"):
                        os.environ["OPENROUTER_API_KEY"] = v.strip().strip("'\"")
    except Exception:
        pass

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
RESTRICTION_MESSAGE = "Sorry, I can only help with CareerNest Hub related queries like jobs, internships, courses, or applications."
UNRELATED_TOPICS = [
    "joke", "jokes", "movie", "movies", "song", "songs", "music",
    "celebrity", "celebrities", "meme", "memes", "cricket", "football",
    "match", "weather", "politics", "random"
]

def get_ai_response(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    prompt_text = str(prompt or "").strip()

    if not prompt_text:
        return RESTRICTION_MESSAGE

    # ADDED: Keyword restriction (safe filter before API call)
    allowed_keywords = ["job", "internship", "course", "career", "application", "placement"]
    keyword_pattern = r"\b(?:job|internship|course|career|application|placement)s?\b"
    unrelated_pattern = r"\b(?:" + "|".join(re.escape(word) for word in UNRELATED_TOPICS) + r")\b"

    if not re.search(keyword_pattern, prompt_text.lower()):
        return RESTRICTION_MESSAGE

    # Existing stricter check retained safely
    if re.search(unrelated_pattern, prompt_text.lower()):
        return RESTRICTION_MESSAGE

    # Existing keyword restriction retained for compatibility
    if not any(word in prompt_text.lower() for word in allowed_keywords):
        return RESTRICTION_MESSAGE

    data = {
        "model": "openrouter/auto",
        "messages": [
            {
                "role": "system",
                "content": """You are CareerNest Assistant for CareerNest Hub platform.

You help with:
- Jobs
- Internships
- Courses
- Applications
- Career guidance

Rules:
- Only answer platform-related questions
- Reject unrelated queries politely
- Keep answers short and professional"""
            },
            {"role": "user", "content": prompt_text}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=45)
    except requests.RequestException as exc:
        return f"Error: {exc}"

    if response.status_code == 200:
        try:
            payload = response.json()
            return payload['choices'][0]['message']['content']
        except (ValueError, KeyError, IndexError, TypeError):
            return f"Error: {response.text}"
    else:
        return f"Error: {response.text}"
