import os
from sqlalchemy import Column, Integer, String, Float, Date
from sqlalchemy.orm import class_mapper
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Producto:
    __tablename__ = 'productos'

    id = Column(Integer, primary_key=True)
    fecha = Column(Date)
    imagen = Column(String)
    nombre = Column(String)
    distribuidor = Column(String)
    precio = Column(Float)

    def as_dict(self):
        return {c.key: getattr(self, c.key) for c in class_mapper(self.__class__).columns}