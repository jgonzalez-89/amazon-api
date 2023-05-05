import os
import ujson
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from datetime import datetime
from flask_cors import CORS
from flask_migrate import Migrate
from sqlalchemy.orm import selectinload
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token
from api.models import db, Producto, Historico, User

load_dotenv()

app = Flask(__name__)
CORS(app)
app.config.from_pyfile("config.py")
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
db.init_app(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)


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


@app.route('/producto/<string:asin>', methods=['GET'])
def get_producto_por_asin(asin):
    try:
        producto = Producto.query.filter_by(ASIN=asin).first()
        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404

        return jsonify(producto.as_dict())
    except Exception as e:
        print("Error al obtener producto por ASIN:", e)
        return jsonify({"error": "Error al obtener producto por ASIN"}), 500


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
