import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:latest")


async def stream_chat(messages: list, model: str = None):
    """Stream a chat request from Ollama asynchronously."""
    model = model or OLLAMA_MODEL
    url = f"{OLLAMA_HOST}/api/chat"

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    chunk = json.loads(line)
                    if "message" in chunk:
                        msg = chunk["message"]
                        yield {
                            "content": msg.get("content", ""),
                            "thinking": msg.get("thinking", ""),
                            "done": chunk.get("done", False)
                        }


async def general_chat(user_prompt: str, history: list = None):
    """Handle normal conversation with history using async streaming."""
    system_prompt = (
        "You are Agent, a helpful and friendly AI assistant. "
        "Answer the user's questions in a clear and concise manner."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    
    if history:
        messages.extend(history)
    
    messages.append({"role": "user", "content": user_prompt})
    
    async for chunk in stream_chat(messages):
        yield chunk


async def check_ollama_health() -> dict:
    """Check if Ollama is reachable and the configured model is available."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/tags")
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
