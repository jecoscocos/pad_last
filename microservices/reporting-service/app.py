from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
PROPERTY_SERVICE_URL = os.environ.get("PROPERTY_SERVICE_URL", "http://localhost:5002")
INQUIRY_SERVICE_URL = os.environ.get("INQUIRY_SERVICE_URL", "http://localhost:5003")
AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:5001")


def verify_token(token: str):
    try:
        response = requests.post(f"{AUTH_SERVICE_URL}/verify", json={"token": token}, timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "reporting-service"}), 200


@app.route("/reports/properties", methods=["GET"])
def properties_report():
    """Generate property summary report"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    if not user or user.get("role") != "agent":
        return jsonify({"error": "Unauthorized"}), 403

    try:
        resp = requests.get(f"{PROPERTY_SERVICE_URL}/properties", timeout=10)
        if resp.status_code != 200:
            return jsonify({"error": "Failed to fetch properties"}), 502
        
        properties = resp.json()
        total = len(properties)
        
        # Статистика по типам
        by_type = {}
        for p in properties:
            ptype = p.get("property_type", "unknown")
            by_type[ptype] = by_type.get(ptype, 0) + 1
        
        # Статистика продажа/аренда
        for_sale = sum(1 for p in properties if p.get("is_for_sale"))
        for_rent = sum(1 for p in properties if p.get("is_for_rent"))
        
        avg_price = sum(p.get("price_eur", 0) for p in properties) / total if total else 0
        
        cities = {}
        for p in properties:
            city = p.get("city", "Unknown")
            cities[city] = cities.get(city, 0) + 1
        
        report = {
            "total": total,
            "by_type": by_type,
            "for_sale": for_sale,
            "for_rent": for_rent,
            "average_price_eur": round(avg_price, 2),
            "by_city": cities,
            "properties": properties  # Добавляем полный список
        }
        return jsonify(report), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/reports/inquiries", methods=["GET"])
def inquiries_report():
    """Generate inquiry summary report"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    if not user or user.get("role") != "agent":
        return jsonify({"error": "Unauthorized"}), 403

    try:
        resp = requests.get(f"{INQUIRY_SERVICE_URL}/inquiries", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if resp.status_code != 200:
            return jsonify({"error": "Failed to fetch inquiries"}), 502
        
        inquiries = resp.json()
        total = len(inquiries)
        by_status = {}
        for inq in inquiries:
            status = inq.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1
        
        report = {
            "total": total,
            "by_status": by_status,
            "inquiries": inquiries  # Добавляем полный список
        }
        return jsonify(report), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5008))
    app.run(host="0.0.0.0", port=port, debug=True)
