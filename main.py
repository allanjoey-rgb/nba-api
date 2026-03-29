from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

NBA_BASE = "https://stats.nba.com/stats"
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")

HEADERS = {
    "Host": "stats.nba.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
    "Origin": "https://www.nba.com",
    "Referer": "https://www.nba.com/",
    "Connection": "keep-alive",
}

@app.route("/")
def home():
    return jsonify({"status": "NBA Proxy funcionando!", "versao": "3.0"})

@app.route("/players/search")
def search_players():
    name = request.args.get("name", "").lower()
    season = request.args.get("season", "2024-25")
    url = f"{NBA_BASE}/commonallplayers"
    params = {"LeagueID": "00", "Season": season, "IsOnlyCurrentSeason": "1"}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        data = r.json()
        headers_list = data["resultSets"][0]["headers"]
        rows = data["resultSets"][0]["rowSet"]
        players = [dict(zip(headers_list, row)) for row in rows]
        filtered = [p for p in players if name in p.get("DISPLAY_FIRST_LAST", "").lower()][:5]
        return jsonify({"players": filtered})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/player/gamelog")
def player_gamelog():
    player_id = request.args.get("player_id")
    season = request.args.get("season", "2024-25")
    url = f"{NBA_BASE}/playergamelog"
    params = {"PlayerID": player_id, "Season": season, "SeasonType": "Regular Season", "LeagueID": "00"}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/player/splits")
def player_splits():
    player_id = request.args.get("player_id")
    season = request.args.get("season", "2024-25")
    last_n = request.args.get("last_n", "0")
    url = f"{NBA_BASE}/playerdashboardbygeneralsplits"
    params = {
        "PlayerID": player_id, "Season": season,
        "SeasonType": "Regular Season", "PerMode": "PerGame",
        "LastNGames": last_n, "MeasureType": "Base",
        "PaceAdjust": "N", "PlusMinus": "N", "Rank": "N",
        "LeagueID": "00", "DateFrom": "", "DateTo": "",
        "GameSegment": "", "Location": "", "Month": "0",
        "OpponentTeamID": "0", "Outcome": "", "PORound": "0",
        "Period": "0", "SeasonSegment": "", "ShotClockRange": "",
        "VsConference": "", "VsDivision": "",
    }
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/ai", methods=["POST"])
def ai_proxy():
    if not GROQ_KEY:
        return jsonify({"error": "GROQ_API_KEY não configurada"}), 500
    try:
        body = request.get_json()
        # Convert Anthropic format to Groq format
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
        # Convert Groq response to Anthropic-like format
        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "Erro ao processar.")
        return jsonify({"content": [{"type": "text", "text": reply}]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
