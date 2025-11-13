from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
PROPERTY_SERVICE_URL = os.environ.get("PROPERTY_SERVICE_URL", "http://localhost:5002")

# Simple in-memory index
_INDEX = []

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "search-service"}), 200

@app.route("/index", methods=["POST"])
def rebuild_index():
    """Rebuild index by fetching properties from property-service"""
    try:
        resp = requests.get(f"{PROPERTY_SERVICE_URL}/properties", timeout=10)
        if resp.status_code != 200:
            return jsonify({"error": "Failed to fetch properties"}), 502
        props = resp.json()
        global _INDEX
        _INDEX = props
        return jsonify({"count": len(_INDEX)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/search", methods=["GET"])
def search():
    q = request.args.get("q", "").lower().strip()
    city = request.args.get("city", "").lower().strip()
    property_type = request.args.get("property_type", "").lower().strip()

    # If index empty, try to fetch
    global _INDEX
    if not _INDEX:
        try:
            r = requests.get(f"{PROPERTY_SERVICE_URL}/properties", timeout=5)
            if r.status_code == 200:
                _INDEX = r.json()
        except:
            pass

    results = []
    for p in _INDEX:
        text = " ".join([str(p.get(k, "")).lower() for k in ("title", "description", "city", "address")])
        if q and q not in text:
            continue
        if city and city not in (p.get("city", "").lower()):
            continue
        if property_type and property_type != (p.get("property_type", "").lower()):
            continue
        results.append(p)

    return jsonify(results), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port, debug=True)
