Comando para construir la imagen de Docker:
` docker build -t my-flask-api . `

Comando para iniciar un contenedor basado en esa imagen:
` docker run -p 5000:5000 my-flask-api `