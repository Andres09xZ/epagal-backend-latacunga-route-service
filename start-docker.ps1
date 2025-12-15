# Script de inicio para Docker - Backend EPAGAL Latacunga
# PowerShell version

Write-Host "🚀 Iniciando Backend EPAGAL Latacunga con Docker..." -ForegroundColor Cyan

# Verificar que Docker esté instalado
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker encontrado: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Docker no está instalado" -ForegroundColor Red
    Write-Host "Por favor instala Docker Desktop desde: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Verificar que Docker Compose esté instalado
try {
    $composeVersion = docker-compose --version
    Write-Host "✅ Docker Compose encontrado: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Docker Compose no está instalado" -ForegroundColor Red
    exit 1
}

# Verificar archivo .env
if (-not (Test-Path .env)) {
    Write-Host "⚠️  Archivo .env no encontrado" -ForegroundColor Yellow
    Write-Host "📝 Creando .env desde .env.example..." -ForegroundColor Cyan
    Copy-Item .env.example .env
    Write-Host "⚠️  IMPORTANTE: Edita el archivo .env con tus credenciales antes de continuar" -ForegroundColor Yellow
    Read-Host "Presiona Enter cuando hayas configurado .env"
}

# Verificar archivos OSRM
if (-not (Test-Path "osrm-ecuador\ecuador-latest.osrm")) {
    Write-Host "❌ Error: No se encontraron archivos OSRM en osrm-ecuador\" -ForegroundColor Red
    Write-Host "Por favor ejecuta setup-osrm.ps1 primero" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Archivos OSRM encontrados" -ForegroundColor Green

# Construir imágenes
Write-Host "`n🔨 Construyendo imágenes Docker..." -ForegroundColor Cyan
docker-compose build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error al construir las imágenes" -ForegroundColor Red
    exit 1
}

# Iniciar servicios
Write-Host "`n🚀 Iniciando servicios..." -ForegroundColor Cyan
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error al iniciar los servicios" -ForegroundColor Red
    exit 1
}

# Esperar a que los servicios estén listos
Write-Host "`n⏳ Esperando a que los servicios estén listos..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# Verificar salud de los servicios
Write-Host "`n🔍 Verificando estado de los servicios..." -ForegroundColor Cyan

try {
    $backendHealth = Invoke-WebRequest -Uri "http://localhost:8081/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ Backend está funcionando correctamente" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Backend no responde todavía, puede tardar un momento más..." -ForegroundColor Yellow
}

try {
    $osrmHealth = Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ OSRM está funcionando correctamente" -ForegroundColor Green
} catch {
    Write-Host "⚠️  OSRM no responde todavía, puede tardar un momento más..." -ForegroundColor Yellow
}

Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "✅ Servicios iniciados correctamente" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📌 URLs disponibles:" -ForegroundColor Yellow
Write-Host "   - API Backend:    http://localhost:8081"
Write-Host "   - Swagger UI:     http://localhost:8081/docs"
Write-Host "   - ReDoc:          http://localhost:8081/redoc"
Write-Host "   - OSRM:           http://localhost:5000"
Write-Host "   - RabbitMQ Admin: http://localhost:15672 (usuario: tesis, password: tesis)"
Write-Host ""
Write-Host "📋 Comandos útiles:" -ForegroundColor Yellow
Write-Host "   - Ver logs:       docker-compose logs -f"
Write-Host "   - Detener:        docker-compose down"
Write-Host "   - Reiniciar:      docker-compose restart"
Write-Host "   - Ver estado:     docker-compose ps"
Write-Host ""
Write-Host "Para ver los logs en tiempo real, ejecuta:" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f" -ForegroundColor White
Write-Host ""

# Preguntar si desea abrir Swagger
$response = Read-Host "¿Deseas abrir Swagger UI en el navegador? (s/n)"
if ($response -eq 's' -or $response -eq 'S') {
    Start-Process "http://localhost:8081/docs"
}
