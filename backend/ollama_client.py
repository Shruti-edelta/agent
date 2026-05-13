import os
import json
import re
import httpx
from dotenv import load_dotenv
from tools import AVAILABLE_TOOLS, TOOL_DEFINITIONS

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
    
    async with httpx.AsyncClient(timeout=None) as client:
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
    """Handle conversation with manual tool support (ReAct pattern)."""
    
    # Detailed system prompt for manual tool calling
    tools_desc = "\n".join([f"- {t['function']['name']}: {t['function']['description']}. Arguments: {t['function']['parameters']['properties']}" for t in TOOL_DEFINITIONS])
    
    system_prompt = (
        "You are Agent, a helpful and friendly AI assistant. "
        "You have access to the following tools:\n"
        f"{tools_desc}\n\n"
        "If you need to use a tool, respond ONLY with the tool call in this format:\n"
        "TOOL: tool_name({\"arg\": \"value\"})\n"
        "Otherwise, respond normally to the user."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_prompt})
    
    try:
        # First call to see if it wants to use a tool (non-streaming for easier parsing)
        url = f"{OLLAMA_HOST}/api/chat"
        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False
        }

        async with httpx.AsyncClient(timeout=None) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            response_text = data.get("message", {}).get("content", "")
            thinking_text = data.get("message", {}).get("thinking", "")
            
            # Simple parsing for TOOL: tool_name({...})
            if "TOOL:" in response_text:
                match = re.search(r"TOOL:\s*(\w+)\((.*)\)", response_text)
                if match:
                    tool_name = match.group(1)
                    args_str = match.group(2)
                    
                    if tool_name in AVAILABLE_TOOLS:
                        try:
                            args = json.loads(args_str)
                            print(f"Manual tool call: {tool_name} with {args}")
                            
                            # Execute tool
                            result = await AVAILABLE_TOOLS[tool_name](**args)
                            
                            # Add tool request and result to history
                            messages.append({"role": "assistant", "content": response_text})
                            messages.append({"role": "user", "content": f"Tool Result: {json.dumps(result)}"})
                            
                            # Final streaming response
                            async for chunk in stream_chat(messages):
                                yield chunk
                            return
                        except Exception as e:
                            print(f"Error parsing tool args: {e}")
            
            # If no tool was detected or parsing failed, yield the original response
            yield {
                "content": response_text,
                "thinking": thinking_text,
                "done": True
            }

    except Exception as e:
        print(f"Error in general_chat: {e}")
        yield {"error": str(e), "done": True}


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
