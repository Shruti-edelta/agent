import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:latest")


def _chat(messages: list, model: str = None) -> str:
    """Send a chat request to Ollama with history and return the assistant's response text."""
    model = model or OLLAMA_MODEL
    url = f"{OLLAMA_HOST}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    return data["message"]["content"].strip()


def general_chat(user_prompt: str, history: list = None) -> str:
    """Handle normal conversation with history."""
    system_prompt = (
        "You are Agent, a helpful and friendly AI assistant. "
        "Answer the user's questions in a clear and concise manner."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    
    if history:
        # history should be a list of {"role": "user"|"assistant", "content": "..."}
        messages.extend(history)
    
    messages.append({"role": "user", "content": user_prompt})
    
    return _chat(messages)


def check_ollama_health() -> dict:
    """Check if Ollama is reachable and the configured model is available."""
    try:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        model_available = any(OLLAMA_MODEL in m for m in models)
        return {
            "reachable": True,
            "model": OLLAMA_MODEL,
            "model_available": model_available,
            "available_models": models,
        }
    except Exception as e:
        return {"reachable": False, "error": str(e)}
