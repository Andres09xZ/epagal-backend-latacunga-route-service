# Dockerfile para Backend EPAGAL Latacunga
FROM python:3.14-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para psycopg2, ortools y shapely
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libgeos-dev \
    libgdal-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Exponer un puerto por defecto (Render asigna PORT dinámico)
EXPOSE 8080

# Variable de entorno para Python
ENV PYTHONUNBUFFERED=1

# Comando para ejecutar la aplicación respetando PORT de Render
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
