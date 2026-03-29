from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")

@app.route("/")
def home():
    return jsonify({"status": "NBA Proxy funcionando!", "versao": "4.0"})

@app.route("/ai", methods=["POST"])
def ai_proxy():
    if not GROQ_KEY:
        return jsonify({"error": "GROQ_API_KEY não configurada"}), 500
    try:
        body = request.get_json()
        system = body.get("system", "")
        messages = body.get("messages", [])
        groq_messages = []
        if system:
            groq_messages.append({"role": "system", "content": system})
        groq_messages.extend(messages)

        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GROQ_KEY}"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": groq_messages,
                "max_tokens": 800,
                "temperature": 0.7
            },
            timeout=30
        )
        data = r.json()
        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "Erro ao processar.")
        return jsonify({"content": [{"type": "text", "text": reply}]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
