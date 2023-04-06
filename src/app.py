import os
from dotenv import load_dotenv
from api.models import Producto
from flask import Flask, jsonify, render_template, request
from datetime import datetime, date
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
import pandas as pd

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
    last_five_dates = Product.query.distinct(
        Product.fecha).order_by(desc(Product.fecha)).limit(5).all()
    last_five_dates = [p.fecha for p in last_five_dates]
    return render_template("index.html", today=today, last_five_dates=last_five_dates)


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

# @app.route('/upload_csv', methods=['POST'])
# def upload_csv():
#     if 'file' not in request.files:
#         return jsonify({'error': 'No se encontró el archivo'}), 400

#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({'error': 'No se seleccionó ningún archivo'}), 400

#     data = pd.read_csv(file)
#     records = data.to_dict(orient='records')

#     try:
#         for record in records:
#             fecha_obj = datetime.strptime(record['fecha'], "%Y-%m-%d").date()
#             producto = Product(
#                 fecha=fecha_obj,
#                 nombre=record['nombre'],
#                 distribuidor=record['distribuidor'],
#                 precio=record['precio'],
#                 imagen=record['imagen']
#             )
#             db.session.add(producto)
#         db.session.commit()
#         return jsonify({'message': 'CSV procesado y añadido'})
#     except Exception as e:
#         print("Error al procesar y guardar los datos del CSV:", e)
#         db.session.rollback()
#         return jsonify({'error': 'Error al procesar y guardar los datos del CSV'}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
