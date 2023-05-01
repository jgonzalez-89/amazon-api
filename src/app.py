from flask import request
import os
import ujson
from dotenv import load_dotenv
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
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token
from collections import defaultdict


load_dotenv()


app = Flask(__name__)
CORS(app)
app.config.from_pyfile("config.py")
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)


class User(db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    def as_dict(self):
        return {
            'id': self.id,
            'email': self.email,
        }


class Producto(db.Model):
    __tablename__ = 'productos'

    id = Column(Integer, primary_key=True)
    imagen = Column(String(255))
    nombre = Column(String(255))
    ASIN = Column(String(255), index=True)
    EAN = Column(Numeric(asdecimal=False), nullable=True, index=True)

    historicos = relationship("Historico", back_populates="producto")

    def as_dict(self):
        historicos_dict = defaultdict(list)
        for historico in self.historicos:
            historicos_dict[historico.id_vendedor].append({
                'fecha': historico.fecha.isoformat(),
                'precio': float(historico.precio),
            })

        return {
            'imagen': self.imagen,
            'nombre': self.nombre,
            'ASIN': self.ASIN,
            'EAN': None if self.EAN is None or (isinstance(self.EAN, float) and math.isnan(self.EAN)) else float(self.EAN),
            'historicos': historicos_dict
        }


class Historico(db.Model):
    __tablename__ = 'historicos'

    id = Column(Integer, primary_key=True)
    fecha = Column(Date, index=True)
    id_vendedor = Column(String(255), nullable=False)
    precio = Column(Float)

    producto_id = Column(Integer, ForeignKey('productos.id'))
    producto = relationship("Producto", back_populates="historicos")

    def as_dict(self):
        return {
            'id': self.id,
            'fecha': self.fecha.isoformat(),
            'id_vendedor': self.id_vendedor,
            'precio': float(self.precio),
        }


@app.route('/')
def home():
    return render_template('index.html')


@app.route("/productos", methods=["GET"])
def get_products():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 100))
        products = Producto.query.paginate(
            page=page, per_page=per_page, error_out=False)
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
            .options(selectinload(Producto.historicos))
            .join(Historico)
            .filter(Historico.fecha == fecha_obj)
            .all()
        )
        result = []
        for producto in productos:
            historicos_grouped = {}
            for h in producto.historicos:
                if h.fecha == fecha_obj:
                    if h.id_vendedor not in historicos_grouped:
                        historicos_grouped[h.id_vendedor] = []
                    historicos_grouped[h.id_vendedor].append({
                        "id": h.id,
                        "precio": h.precio,
                        "fecha": h.fecha.strftime("%Y-%m-%d"),
                    })

            if historicos_grouped:
                result.append({
                    **producto.as_dict(),
                    "historicos": historicos_grouped
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

    try:
        for record in file_content:
            producto_existente = Producto.query.filter_by(
                ASIN=record['ASIN']).first()

            if producto_existente:
                producto = producto_existente
            else:
                producto = Producto(
                    nombre=record['nombre'],
                    ASIN=record['ASIN'],
                    imagen=record['imagen'],
                    EAN=record['EAN']
                )
                db.session.add(producto)
                db.session.flush()

            for vendedor_id, historicos_vendedor in record['historicos'].items():
                for historico_data in historicos_vendedor:
                    fecha_obj = datetime.strptime(
                        historico_data['fecha'], "%d-%m-%Y").date()
                    historico = Historico(
                        fecha=fecha_obj,
                        id_vendedor=vendedor_id,
                        precio=historico_data['precio'],
                        producto_id=producto.id
                    )
                    db.session.add(historico)

        db.session.commit()
        return jsonify({'message': 'JSON procesado y añadido'})
    except Exception as e:
        print("Error al procesar y guardar los datos del JSON:", e)
        db.session.rollback()
        return jsonify({'error': 'Error al procesar y guardar los datos del JSON'}), 500



@app.route('/register', methods=['POST'])
def register():
    email = request.json.get('email')
    password = request.json.get('password')

    if not email or not password:
        return jsonify({"error": "Email y contraseña son requeridos"}), 400

    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({"error": "El correo electrónico ya está registrado"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify(new_user.as_dict()), 201


@app.route('/login', methods=['POST'])
def login():
    email = request.json.get('email')
    password = request.json.get('password')

    if not email or not password:
        return jsonify({"error": "Email y contraseña son requeridos"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Correo electrónico o contraseña incorrectos"}), 401

    access_token = create_access_token(identity=user.id)
    return jsonify({"token": access_token})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
