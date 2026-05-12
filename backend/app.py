import os
import json
import asyncio
from quart import Quart, request, jsonify, Response
from dotenv import load_dotenv
import ollama_client

load_dotenv()

app = Quart(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "chatbot-dev-secret-key")
app.config["RESPONSE_TIMEOUT"] = None

ALLOWED_ORIGINS = {
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.0.104:5173",
}

def get_cors_headers(origin: str) -> dict:
    """Return CORS headers if origin is allowed."""
    if origin in ALLOWED_ORIGINS:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Credentials": "true",
        }
    return {}


@app.after_request
async def apply_cors(response):
    """Attach CORS headers to every response."""
    origin = request.headers.get("Origin", "")
    for key, val in get_cors_headers(origin).items():
        response.headers[key] = val
    return response


@app.route("/api/health", methods=["GET", "OPTIONS"])
async def health():
    if request.method == "OPTIONS":
        return Response("", status=204)
    ollama_status = await ollama_client.check_ollama_health()
    return jsonify({"status": "ok", "ollama": ollama_status})


@app.route("/api/chat", methods=["POST", "OPTIONS"])
async def chat():
    if request.method == "OPTIONS":
        return Response("", status=204)

    data = await request.get_json()
    prompt = data.get("prompt", "").strip()
    history = data.get("messages", [])

    if not prompt:
        return jsonify({"success": False, "message": "Prompt cannot be empty."}), 400

    origin = request.headers.get("Origin", "")
    cors_headers = get_cors_headers(origin)

    async def generate():
        """Fully async SSE generator — each chat runs concurrently."""
        try:
            async for chunk in ollama_client.general_chat(prompt, history):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
        **cors_headers,  # Inject CORS headers directly into stream response
    }
    response = Response(generate(), status=200, headers=headers)
    response.timeout = None  # Disable Quart's default 60-second timeout
    return response


if __name__ == "__main__":
    from hypercorn.config import Config
    import hypercorn.asyncio

    config = Config()
    config.bind = ["0.0.0.0:5001"]
    config.use_reloader = True
    asyncio.run(hypercorn.asyncio.serve(app, config))
