from flask import Flask, render_template, request, jsonify
import requests
import os
from flask import send_from_directory

app = Flask(__name__, static_folder="static")
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:5001").rstrip("/")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat_proxy():
    try:
        r = requests.post(
            BACKEND_URL + "/api/chat",
            json=request.get_json(silent=True) or {},
            timeout=90
        )
        return jsonify(r.json()), r.status_code
    except requests.RequestException:
        return jsonify({"reply": "إيفا مش قادرة تتصل بالذكاء دلوقتي، جرّب تاني."}), 502
    except ValueError:
        return jsonify({"reply": "حصل خطأ في استجابة الذكاء."}), 502

@app.route("/eva_queen.webp")
def eva_image():
    return send_from_directory(app.static_folder, "eva_queen.webp")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
