import os
from dotenv import load_dotenv
from src.api.models import Producto
from flask import Flask, jsonify, render_template
from datetime import datetime, date
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc

load_dotenv()

app = Flask(__name__)
CORS(app)
app.config.from_pyfile("config.py")
db = SQLAlchemy(app)

class Product(db.Model, Producto):
    pass

@app.route("/")
def sitemap():
    today = date.today()
    last_five_dates = Product.query.distinct(Product.fecha).order_by(desc(Product.fecha)).limit(5).all()
    last_five_dates = [p.fecha for p in last_five_dates]
    return render_template("index.html", today=today, last_five_dates=last_five_dates)

# @app.route("/")
# def sitemap():
#     today = date.today()
#     return render_template("index.html", today=today)

@app.route("/productos", methods=["GET"])
def get_products():
    try:
        products = Product.query.all()
        return jsonify([p.as_dict() for p in products])
    except Exception as e:
        print("Error al obtener productos:", e)
        return jsonify({"error": "Error al obtener productos"}), 500

@app.route('/fecha/<string:fecha>', methods=['GET'])
def get_productos_por_fecha(fecha):
    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Formato de fecha inválido"}), 400

    try:
        productos = Product.query.filter_by(fecha=fecha_obj).all()
        return jsonify([p.as_dict() for p in productos])
    except Exception as e:
        print("Error al obtener productos por fecha:", e)
        return jsonify({"error": "Error al obtener productos por fecha"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)