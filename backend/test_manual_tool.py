import asyncio
import httpx
import json
import re

OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "deepseek-r1:latest"

async def test_manual_pattern():
    print(f"Testing manual tool pattern with {OLLAMA_MODEL}...")
    
    system_prompt = (
        "You are a helpful assistant. You have a tool: get_weather(location). "
        "If asked about weather, respond ONLY with: TOOL: get_weather({\"location\": \"city\"})"
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "whta is youer name?"}
    ]
    
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False
    }
    
    async with httpx.AsyncClient(timeout=None) as client:
        resp = await client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
        data = resp.json()
        content = data.get("message", {}).get("content", "")
        print(f"Model response: {content}")
        
        if "TOOL:" in content:
            print("Success: Tool call detected!")
        else:
            print("Failed: No tool call detected.")

if __name__ == "__main__":
    asyncio.run(test_manual_pattern())
