from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os
import json

app = Flask(__name__)
CORS(app)

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")

@app.route("/")
def home():
    return jsonify({"status": "NBA Proxy funcionando!", "versao": "7.0"})

@app.route("/ask", methods=["POST"])
def ask():
    if not GROQ_KEY:
        return jsonify({"error": "GROQ_API_KEY não configurada"}), 500
    try:
        body = request.get_json()
        question = body.get("question", "")

        system = """Você é um especialista em NBA com conhecimento profundo de estatísticas até 2024-25.

Responda SEMPRE com um JSON válido neste formato exato:

{
  "resposta": "Texto da resposta em português brasileiro, animado e informativo. Use no máximo 3 parágrafos curtos.",
  "tipo": "jogador|comparacao|ranking|geral",
  "dados": {
    "jogadores": [
      {
        "nome": "Nome Completo",
        "time": "SIGLA",
        "posicao": "PG/SG/SF/PF/C",
        "pts": 0.0,
        "reb": 0.0,
        "ast": 0.0,
        "stl": 0.0,
        "blk": 0.0,
        "fg_pct": 0.0,
        "fg3_pct": 0.0,
        "gp": 0
      }
    ],
    "ranking": [
      {
        "posicao": 1,
        "nome": "Nome",
        "time": "SIGLA",
        "valor": 0.0,
        "stat": "PTS"
      }
    ],
    "stat_destaque": "PTS|REB|AST|STL|BLK",
    "temporada": "2024-25"
  }
}

REGRAS:
- Sempre retorne JSON válido, nunca texto puro
- Use dados reais e precisos da NBA temporada 2024-25
- Para perguntas sobre um jogador: preencha "jogadores" com 1 jogador
- Para comparações: preencha "jogadores" com 2 jogadores
- Para rankings/líderes: preencha "ranking" com top 8 jogadores
- Para perguntas gerais: tipo="geral", dados vazios
- A resposta deve ser em português brasileiro
- Nunca inclua markdown ou texto fora do JSON"""

        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GROQ_KEY}"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": question}
                ],
                "max_tokens": 1500,
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            },
            timeout=30
        )
        data = r.json()
        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        
        try:
            parsed = json.loads(reply)
        except:
            parsed = {"resposta": reply, "tipo": "geral", "dados": {}}
        
        return jsonify(parsed)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
