from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
BDL_KEY = os.environ.get("BDL_API_KEY", "")
BDL_BASE = "https://api.balldontlie.io/nba/v1"

def bdl_headers():
    return {"Authorization": BDL_KEY}

@app.route("/")
def home():
    return jsonify({"status": "NBA Proxy funcionando!", "versao": "8.0"})

@app.route("/players/search")
def search_players():
    name = request.args.get("name", "")
    try:
        r = requests.get(f"{BDL_BASE}/players", headers=bdl_headers(), params={"search": name, "per_page": 5}, timeout=15)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/players/stats")
def player_stats():
    player_id = request.args.get("player_id", "")
    season = request.args.get("season", "2024")
    try:
        r = requests.get(f"{BDL_BASE}/season_averages", headers=bdl_headers(), params={"player_ids[]": player_id, "season": season}, timeout=15)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/leaders")
def leaders():
    stat = request.args.get("stat", "pts")
    season = request.args.get("season", "2024")
    try:
        r = requests.get(f"{BDL_BASE}/season_averages", headers=bdl_headers(), params={"season": season, "per_page": 100}, timeout=15)
        data = r.json()
        players_data = data.get("data", [])
        players_data = [p for p in players_data if p.get("games_played", 0) >= 20]
        players_data.sort(key=lambda x: x.get(stat, 0), reverse=True)
        return jsonify({"data": players_data[:10]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/players/info")
def player_info():
    player_id = request.args.get("player_id", "")
    try:
        r = requests.get(f"{BDL_BASE}/players/{player_id}", headers=bdl_headers(), timeout=15)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/scores")
def scores():
    try:
        from datetime import datetime, timedelta
        dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(3)]
        params = {}
        for i, d in enumerate(dates):
            params[f"dates[]"] = d
        r = requests.get(f"{BDL_BASE}/games", headers=bdl_headers(), params={"dates[]": dates, "per_page": 15}, timeout=15)
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
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_KEY}"},
            json={"model": "llama-3.3-70b-versatile", "messages": groq_messages, "max_tokens": 800, "temperature": 0.7},
            timeout=30
        )
        data = r.json()
        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "Erro ao processar.")
        return jsonify({"content": [{"type": "text", "text": reply}]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
