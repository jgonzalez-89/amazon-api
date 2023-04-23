import os
import ujson
from dotenv import load_dotenv
# from api.models import Producto
from flask import Flask, jsonify, render_template, request
from datetime import datetime, date
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import desc
import pandas as pd
import math

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, class_mapper
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Numeric
from sqlalchemy.orm import selectinload


load_dotenv()

app = Flask(__name__)
CORS(app)
app.config.from_pyfile("config.py")
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Producto(db.Model):
    __tablename__ = 'productos'

    id = Column(Integer, primary_key=True)
    imagen = Column(String(255))
    nombre = Column(String(255))
    distribuidor = Column(String(255))
    ASIN = Column(String(255), index=True)
    EAN = Column(Numeric(asdecimal=False), nullable=True, index=True)

    precios_historicos = relationship(
        "PrecioHistorico", back_populates="producto")

    def as_dict(self):
        precios_historicos = [precio.as_dict() for precio in self.precios_historicos]
        return {
            'id': self.id,
            'imagen': self.imagen,
            'nombre': self.nombre,
            'distribuidor': self.distribuidor,
            'ASIN': self.ASIN,
            'EAN': None if self.EAN is None or (isinstance(self.EAN, float) and math.isnan(self.EAN)) else float(self.EAN),
            'precios_historicos': precios_historicos
        }


class PrecioHistorico(db.Model):
    __tablename__ = 'precios_historicos'

    id = Column(Integer, primary_key=True)
    fecha = Column(Date, index=True)
    precio = Column(Float)

    producto_id = Column(Integer, ForeignKey('productos.id'))
    producto = relationship("Producto", back_populates="precios_historicos")

    def as_dict(self):
        return {
            'id': self.id,
            'fecha': self.fecha.isoformat(),
            'precio': float(self.precio),
            # 'producto_id': self.producto_id
        }


from flask import request

@app.route("/productos", methods=["GET"])
def get_products():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 100))
        products = Producto.query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify([p.as_dict() for p in products.items])
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
        productos = (
            Producto.query
            .options(selectinload(Producto.precios_historicos))
            .join(PrecioHistorico)
            .filter(PrecioHistorico.fecha == fecha_obj)
            .all()
        )
        result = []
        for producto in productos:
            precio = next(
                (ph for ph in producto.precios_historicos if ph.fecha == fecha_obj), None)
            if precio is not None:
                result.append({
                    **producto.as_dict(),
                    "precio": precio.precio,
                    "fecha": precio.fecha.strftime("%Y-%m-%d")
                })
        return jsonify(result)
    except Exception as e:
        print("Error al obtener productos por fecha:", e)
        return jsonify({"error": "Error al obtener productos por fecha"}), 500


@app.route('/file', methods=['POST'])
def upload_json():
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No se seleccionó ningún archivo'}), 400

        file_content = ujson.load(file)

    elif request.is_json:
        file_content = request.get_json()

    else:
        return jsonify({'error': 'No se encontró el archivo o el JSON en crudo'}), 400

    if not isinstance(file_content, list):
        file_content = [file_content]

    data = pd.DataFrame.from_dict(file_content)
    records = data.to_dict(orient='records')

    try:
        for record in records:
            fecha_obj = datetime.strptime(record['fecha'], "%d-%m-%Y").date()
            producto_existente = Producto.query.filter_by(
                ASIN=record['ASIN'], distribuidor=record['distribuidor']).first()

            if producto_existente:
                producto = producto_existente
            else:
                producto = Producto(
                    nombre=record['nombre'],
                    distribuidor=record['distribuidor'],
                    ASIN=record['ASIN'],
                    imagen=record['imagen'],
                    EAN=record['EAN']
                )
                db.session.add(producto)
                db.session.flush()

            precio_historico = PrecioHistorico(
                fecha=fecha_obj,
                precio=record['precio'],
                producto_id=producto.id
            )
            db.session.add(precio_historico)

        db.session.commit()
        return jsonify({'message': 'JSON procesado y añadido'})
    except Exception as e:
        print("Error al procesar y guardar los datos del JSON:", e)
        db.session.rollback()
        return jsonify({'error': 'Error al procesar y guardar los datos del JSON'}), 500


@app.route('/fecha/<string:fecha>', methods=['DELETE'])
def delete_productos_por_fecha(fecha):
    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Formato de fecha inválido"}), 400

    try:
        productos = Producto.query.filter_by(fecha=fecha_obj).all()
        if not productos:
            return jsonify({'error': 'No se encontraron productos para la fecha especificada'}), 404

        for producto in productos:
            db.session.delete(producto)
        db.session.commit()
        return jsonify({'message': 'Productos eliminados exitosamente'})
    except Exception as e:
        print("Error al eliminar productos por fecha:", e)
        db.session.rollback()
        return jsonify({"error": "Error al eliminar productos por fecha"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
