import os
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import class_mapper, relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Producto(Base):
    __tablename__ = 'productos'

    id = Column(Integer, primary_key=True)
    imagen = Column(String)
    nombre = Column(String)
    distribuidor = Column(String)
    ASIN = Column(String)
    EAN = Column(String)

    precios_historicos = relationship("PrecioHistorico", back_populates="producto")

    def as_dict(self):
        return {c.key: getattr(self, c.key) for c in class_mapper(self.__class__).columns}

class PrecioHistorico(Base):
    __tablename__ = 'precios_historicos'

    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey('productos.id'))
    fecha = Column(Date)
    precio = Column(Float)

    producto = relationship("Producto", back_populates="precios_historicos")

    def as_dict(self):
        return {c.key: getattr(self, c.key) for c in class_mapper(self.__class__).columns}
