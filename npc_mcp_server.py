# Gerekli MCP SDK importlarını buraya ekle
# Unity'den gelecek güncel durumu tutacak global veya sınıf seviyesi değişkenler
import json
import requests  # Yerel Ollama API'sine istek atmak için
from flask import Flask, jsonify, request
from mcp.server.mcpserver import MCPServer

app = Flask(__name__)
mcp = MCPServer("NpcServer")
current_npc_state = {}
current_legal_actions = []


@mcp.tool()
def get_npc_state() -> dict:
    return current_npc_state  #


@mcp.tool()
def get_legal_actions() -> list[str]:
    return current_legal_actions  # [cite: 7]


@mcp.tool()
def get_environment_context() -> dict:
    return {"nearest_cover_distance": 4.2, "objective_under_threat": True}  # [cite: 7]


def request_ai_decision():
    # 1. MCP araçlarıyla güncel bağlamı çek[cite: 7]
    state = get_npc_state()
    actions = get_legal_actions()

    # 2. Ollama'ya gönderilecek sistem promptu
    prompt = f"""
    Mevcut NPC Durumu: {state}
    Seçilebilecek Geçerli Eylemler: {actions}
    
    Sadece yukarıdaki geçerli eylemlerden o anki duruma en uygun olanı seç. 
    Cevabını kesinlikle aşağıdaki JSON şemasına uygun şekilde ver:
    {{
        "action": "EYLEM_ADI",
        "confidence": 0.85,
        "reason": "Kısa taktiksel açıklama"
    }}
    """

    # 3. Yerel Ollama servisine (qwen2.5:7b) istek at
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:7b",
            "prompt": prompt,
            "stream": False,
            "format": "json",  # Modeli sadece JSON üretmeye zorlar[cite: 8]
        },
    )

    # 4. Yapılandırılmış sonucu döndür[cite: 7]
    return json.loads(response.json()["response"])


@app.route("/decision", methods=["POST"])
def decision_endpoint():
    global current_npc_state, current_legal_actions
    data = request.json
    if data:
        current_npc_state = data.get("state", {})
        current_legal_actions = data.get("actions", [])

    result = request_ai_decision()
    return jsonify(result)


if __name__ == "__main__":
    print("Sunucu 5000 portunda başlatılıyor...")
    app.run(port=5000)
