import os
import json
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv
import ollama_client

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "chatbot-dev-secret-key")
CORS(app, supports_credentials=True, origins=["http://localhost:5173", "http://127.0.0.1:5173","http://192.168.0.104:5173"])

@app.route("/api/health", methods=["GET"])
def health():
    """Health check — also reports Ollama status."""
    ollama_status = ollama_client.check_ollama_health()
    return jsonify({"status": "ok", "ollama": ollama_status})


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    prompt = data.get("prompt", "").strip()
    history = data.get("messages", [])
    
    if not prompt:
        return jsonify({"success": False, "message": "Prompt cannot be empty."}), 400

    def generate():
        try:
            for chunk in ollama_client.general_chat(prompt, history):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
