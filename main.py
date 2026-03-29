from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")

RAPID_HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "nba-api-free-data.p.rapidapi.com"
}

@app.route("/")
def home():
    return jsonify({"status": "NBA Proxy funcionando!", "versao": "5.0"})

@app.route("/players/search")
def search_players():
    name = request.args.get("name", "")
    try:
        r = requests.get(
            "https://nba-api-free-data.p.rapidapi.com/nba-player-listing/v1/data",
            headers=RAPID_HEADERS,
            params={"name": name},
            timeout=15
        )
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/players/stats")
def player_stats():
    player_id = request.args.get("player_id", "")
    season = request.args.get("season", "2024-25")
    try:
        r = requests.get(
            "https://nba-api-free-data.p.rapidapi.com/nba-player-info/v1/data",
            headers=RAPID_HEADERS,
            params={"id": player_id},
            timeout=15
        )
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/leaders")
def leaders():
    stat = request.args.get("stat", "points")
    season = request.args.get("season", "2024-25")
    try:
        r = requests.get(
            "https://nba-api-free-data.p.rapidapi.com/nba-player-listing/v1/data",
            headers=RAPID_HEADERS,
            params={"season": season},
            timeout=15
        )
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/scores")
def scores():
    date = request.args.get("date", "")
    try:
        r = requests.get(
            "https://nba-api-free-data.p.rapidapi.com/nba-score/v1/data",
            headers=RAPID_HEADERS,
            params={"date": date},
            timeout=15
        )
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/standings")
def standings():
    try:
        r = requests.get(
            "https://nba-api-free-data.p.rapidapi.com/nba-standings/v1/data",
            headers=RAPID_HEADERS,
            timeout=15
        )
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
