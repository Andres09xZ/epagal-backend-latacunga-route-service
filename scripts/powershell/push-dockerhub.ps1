# Script para construir y subir imagen a Docker Hub
# EPAGAL Backend - Latacunga Route Service

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  EPAGAL - Push to Docker Hub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Solicitar nombre de usuario de Docker Hub
$dockerUsername = Read-Host "Ingresa tu usuario de Docker Hub"

if ([string]::IsNullOrWhiteSpace($dockerUsername)) {
    Write-Host "Error: Debes ingresar un nombre de usuario" -ForegroundColor Red
    exit 1
}

# Nombre de la imagen
$imageName = "epagal-backend-latacunga"
$version = "latest"
$fullImageName = "${dockerUsername}/${imageName}:${version}"

Write-Host ""
Write-Host "Configuracion:" -ForegroundColor Yellow
Write-Host "  Usuario Docker Hub: $dockerUsername" -ForegroundColor White
Write-Host "  Nombre de imagen:   $imageName" -ForegroundColor White
Write-Host "  Tag:                $version" -ForegroundColor White
Write-Host "  Imagen completa:    $fullImageName" -ForegroundColor Green
Write-Host ""

# Confirmar
$confirm = Read-Host "Continuar? (s/n)"
if ($confirm -ne "s" -and $confirm -ne "S") {
    Write-Host "Operacion cancelada" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Paso 1: Iniciando sesion en Docker Hub..." -ForegroundColor Cyan
docker login
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: No se pudo iniciar sesion en Docker Hub" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Paso 2: Construyendo imagen Docker..." -ForegroundColor Cyan
Write-Host "  Esto puede tardar varios minutos..." -ForegroundColor Yellow
docker build -t $fullImageName .
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: No se pudo construir la imagen" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Paso 3: Verificando imagen construida..." -ForegroundColor Cyan
docker images | Select-String $imageName

Write-Host ""
Write-Host "Paso 4: Subiendo imagen a Docker Hub..." -ForegroundColor Cyan
Write-Host "  Esto puede tardar varios minutos..." -ForegroundColor Yellow
docker push $fullImageName
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: No se pudo subir la imagen a Docker Hub" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Imagen subida exitosamente!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Imagen disponible en:" -ForegroundColor Cyan
Write-Host "  docker pull $fullImageName" -ForegroundColor White
Write-Host ""
Write-Host "URL Docker Hub:" -ForegroundColor Cyan
Write-Host "  https://hub.docker.com/r/$dockerUsername/$imageName" -ForegroundColor White
Write-Host ""
Write-Host "Proceso completado!" -ForegroundColor Green
