# Imagen base ligera con Python
FROM python:3.11-slim

# Crear directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar dependencias e instalarlas
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copiar todos los archivos del proyecto (main.py, database.py, etc.)
COPY .. .

# Exponer puerto 80 (ideal para Fargate / ECS)
EXPOSE 80

# Ejecutar la aplicación con Uvicorn, escuchando en 0.0.0.0:80
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
