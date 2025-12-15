#!/bin/bash
# Script de inicio para Docker - Backend EPAGAL Latacunga

set -e

echo "🚀 Iniciando Backend EPAGAL Latacunga con Docker..."

# Verificar que Docker esté instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker no está instalado"
    echo "Por favor instala Docker Desktop desde: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Verificar que Docker Compose esté instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose no está instalado"
    exit 1
fi

echo "✅ Docker y Docker Compose encontrados"

# Verificar archivo .env
if [ ! -f .env ]; then
    echo "⚠️  Archivo .env no encontrado"
    echo "📝 Creando .env desde .env.example..."
    cp .env.example .env
    echo "⚠️  IMPORTANTE: Edita el archivo .env con tus credenciales antes de continuar"
    read -p "Presiona Enter cuando hayas configurado .env..."
fi

# Verificar archivos OSRM
if [ ! -f osrm-ecuador/ecuador-latest.osrm ]; then
    echo "❌ Error: No se encontraron archivos OSRM en osrm-ecuador/"
    echo "Por favor ejecuta setup-osrm.ps1 primero"
    exit 1
fi

echo "✅ Archivos OSRM encontrados"

# Construir imágenes
echo "🔨 Construyendo imágenes Docker..."
docker-compose build

# Iniciar servicios
echo "🚀 Iniciando servicios..."
docker-compose up -d

# Esperar a que los servicios estén listos
echo "⏳ Esperando a que los servicios estén listos..."
sleep 10

# Verificar salud de los servicios
echo "🔍 Verificando estado de los servicios..."

if curl -f http://localhost:8081/health &> /dev/null; then
    echo "✅ Backend está funcionando correctamente"
else
    echo "⚠️  Backend no responde todavía, puede tardar un momento más..."
fi

if curl -f http://localhost:5000/health &> /dev/null; then
    echo "✅ OSRM está funcionando correctamente"
else
    echo "⚠️  OSRM no responde todavía, puede tardar un momento más..."
fi

echo ""
echo "========================================="
echo "✅ Servicios iniciados correctamente"
echo "========================================="
echo ""
echo "📌 URLs disponibles:"
echo "   - API Backend:    http://localhost:8081"
echo "   - Swagger UI:     http://localhost:8081/docs"
echo "   - ReDoc:          http://localhost:8081/redoc"
echo "   - OSRM:           http://localhost:5000"
echo "   - RabbitMQ Admin: http://localhost:15672 (usuario: tesis, password: tesis)"
echo ""
echo "📋 Comandos útiles:"
echo "   - Ver logs:       docker-compose logs -f"
echo "   - Detener:        docker-compose down"
echo "   - Reiniciar:      docker-compose restart"
echo "   - Ver estado:     docker-compose ps"
echo ""
echo "Para ver los logs en tiempo real, ejecuta:"
echo "   docker-compose logs -f"
echo ""
