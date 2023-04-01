# Utiliza la imagen oficial de Python como base
FROM python:3.9-slim

# Establece un directorio de trabajo
WORKDIR /app

# Instalar dependencias para compilar psycopg2
RUN apt-get update && \
    apt-get install -y gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copia los archivos de requerimientos e instálalos
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia la carpeta src con el código de la aplicación
COPY src/ src/

ENV DATABASE_URL=postgresql://mypinga:2xauq08ifk8XXs0Hpl8ijHKsGSNpb2W1@dpg-cgjacvgrjeniuke5lqvg-a.frankfurt-postgres.render.com/products_box5


# Expone el puerto en el que se ejecutará la aplicación
EXPOSE 5000

# Inicia la aplicación con Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "src.wsgi:app"]
