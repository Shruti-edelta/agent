import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:latest")


def stream_chat(messages: list, model: str = None):
    """Stream a chat request from Ollama."""
    model = model or OLLAMA_MODEL
    url = f"{OLLAMA_HOST}/api/chat"

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
    }
    
    response = requests.post(url, json=payload, stream=True, timeout=120)
    response.raise_for_status()

    for line in response.iter_lines():
        if line:
            chunk = json.loads(line)
            if "message" in chunk:
                msg = chunk["message"]
                yield {
                    "content": msg.get("content", ""),
                    "thinking": msg.get("thinking", ""),
                    "done": chunk.get("done", False)
                }


def general_chat(user_prompt: str, history: list = None):
    """Handle normal conversation with history using streaming."""
    system_prompt = (
        "You are Agent, a helpful and friendly AI assistant. "
        "Answer the user's questions in a clear and concise manner."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    
    if history:
        # history should be a list of {"role": "user"|"assistant", "content": "..."}
        messages.extend(history)
    
    messages.append({"role": "user", "content": user_prompt})
    
    # We yield from the generator
    yield from stream_chat(messages)


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
