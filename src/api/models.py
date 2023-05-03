import math
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from collections import defaultdict
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


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
