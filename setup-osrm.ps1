# ============================================================================
# Script de configuracion de OSRM para Ecuador
# Proyecto: Backend Latacunga Clean
# ============================================================================

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "     CONFIGURACION DE OSRM PARA LATACUNGA - ECUADOR       " -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Variables de configuración
$OSRM_DIR = "osrm-ecuador"
$DATA_FILE = "ecuador-latest.osm.pbf"
$CONTAINER_NAME = "latacunga_routing"
$PORT = 5000

# Paso 1: Limpiar contenedores anteriores
Write-Host "[1/7] Limpiando contenedores OSRM anteriores..." -ForegroundColor Yellow
docker stop $CONTAINER_NAME 2>$null
docker rm $CONTAINER_NAME 2>$null
docker container prune -f 2>$null

# Paso 2: Crear/verificar directorio
Write-Host "[2/7] Verificando directorio de trabajo..." -ForegroundColor Yellow
if (-Not (Test-Path $OSRM_DIR)) {
    New-Item -ItemType Directory -Path $OSRM_DIR | Out-Null
    Write-Host "  - Directorio creado: $OSRM_DIR" -ForegroundColor Green
}
else {
    Write-Host "  - Directorio ya existe: $OSRM_DIR" -ForegroundColor Green
}

Set-Location $OSRM_DIR

# Paso 3: Descargar datos (si no existen)
if (-Not (Test-Path $DATA_FILE)) {
    Write-Host "[3/7] Descargando datos de Ecuador (~180 MB)..." -ForegroundColor Yellow
    Write-Host "  Fuente: https://download.geofabrik.de/south-america/" -ForegroundColor Gray
    
    try {
        Invoke-WebRequest -Uri "https://download.geofabrik.de/south-america/ecuador-latest.osm.pbf" `
                          -OutFile $DATA_FILE `
                          -ErrorAction Stop
        Write-Host "  - Descarga completada" -ForegroundColor Green
    }
    catch {
        Write-Host "  X Error en la descarga: $_" -ForegroundColor Red
        exit 1
    }
}
else {
    $fileSize = (Get-Item $DATA_FILE).Length / 1MB
    Write-Host "[3/7] Datos ya descargados ($([math]::Round($fileSize, 2)) MB)" -ForegroundColor Green
}

# Paso 4: Extraer datos con perfil de carro
Write-Host "[4/7] Extrayendo datos con perfil de carro..." -ForegroundColor Yellow
Write-Host "  (Esto puede tomar 5-10 minutos)" -ForegroundColor Gray

docker run -t --rm `
  -v "${PWD}:/data" `
  ghcr.io/project-osrm/osrm-backend `
  osrm-extract -p /opt/car.lua /data/$DATA_FILE

if ($LASTEXITCODE -ne 0) {
    Write-Host "  X Error en la extraccion" -ForegroundColor Red
    exit 1
}
Write-Host "  - Extraccion completada" -ForegroundColor Green

# Paso 5: Particionar el grafo
Write-Host "[5/7] Particionando el grafo de rutas..." -ForegroundColor Yellow

docker run -t --rm `
  -v "${PWD}:/data" `
  ghcr.io/project-osrm/osrm-backend `
  osrm-partition /data/ecuador-latest.osrm

if ($LASTEXITCODE -ne 0) {
    Write-Host "  X Error en la particion" -ForegroundColor Red
    exit 1
}
Write-Host "  - Particion completada" -ForegroundColor Green

# Paso 6: Personalizar el grafo
Write-Host "[6/7] Personalizando el grafo..." -ForegroundColor Yellow

docker run -t --rm `
  -v "${PWD}:/data" `
  ghcr.io/project-osrm/osrm-backend `
  osrm-customize /data/ecuador-latest.osrm

if ($LASTEXITCODE -ne 0) {
    Write-Host "  X Error en la personalizacion" -ForegroundColor Red
    exit 1
}
Write-Host "  - Personalizacion completada" -ForegroundColor Green

# Paso 7: Iniciar servidor OSRM
Write-Host "[7/7] Iniciando servidor OSRM..." -ForegroundColor Yellow

docker run -d --name $CONTAINER_NAME `
  -p ${PORT}:5000 `
  -v "${PWD}:/data" `
  --restart unless-stopped `
  ghcr.io/project-osrm/osrm-backend `
  osrm-routed --algorithm mld /data/ecuador-latest.osrm

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ Error al iniciar el servidor" -ForegroundColor Red
    exit 1
}

# Esperar a que el servidor inicie
Write-Host "  Esperando a que el servidor inicie..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Verificar estado
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "                   VERIFICACION                            " -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

$container = docker ps --filter "name=$CONTAINER_NAME" --format "{{.Names}}"
if ($container -eq $CONTAINER_NAME) {
    Write-Host "- Contenedor: $CONTAINER_NAME esta corriendo" -ForegroundColor Green
    Write-Host "- Puerto: $PORT" -ForegroundColor Green
    
    # Probar una ruta de ejemplo
    Write-Host "`nProbando ruta de ejemplo..." -ForegroundColor Yellow
    Write-Host "  Depósito EPAGAL (-78.613, -0.936) -> Botadero Inchapo (-78.663, -0.949)" -ForegroundColor Gray
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:${PORT}/route/v1/driving/-78.613,-0.936;-78.663,-0.949?overview=simplified" -UseBasicParsing
        $result = $response.Content | ConvertFrom-Json
        
        if ($result.code -eq "Ok") {
            $distance = [math]::Round($result.routes[0].distance / 1000, 2)
            $duration = [math]::Round($result.routes[0].duration / 60, 1)
            
            Write-Host "`n- OSRM esta funcionando correctamente!" -ForegroundColor Green
            Write-Host "  Distancia: $distance km" -ForegroundColor Cyan
            Write-Host "  Tiempo: $duration minutos" -ForegroundColor Cyan
        }
        else {
            Write-Host "`n! OSRM respondio pero con error: $($result.code)" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "`n! No se pudo conectar a OSRM todavia (puede necesitar mas tiempo)" -ForegroundColor Yellow
    }
}
else {
    Write-Host "X El contenedor no esta corriendo" -ForegroundColor Red
    docker logs $CONTAINER_NAME
    exit 1
}

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "          - CONFIGURACION COMPLETADA CON EXITO            " -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Green

Write-Host "Comandos útiles:" -ForegroundColor Cyan
Write-Host "  Ver logs:     docker logs $CONTAINER_NAME" -ForegroundColor White
Write-Host "  Detener:      docker stop $CONTAINER_NAME" -ForegroundColor White
Write-Host "  Iniciar:      docker start $CONTAINER_NAME" -ForegroundColor White
Write-Host "  Eliminar:     docker rm -f $CONTAINER_NAME" -ForegroundColor White
Write-Host "`n  URL API:      http://localhost:${PORT}" -ForegroundColor Yellow
Write-Host "  Ejemplo:      http://localhost:${PORT}/route/v1/driving/-78.613,-0.936;-78.663,-0.949`n" -ForegroundColor White

# Volver al directorio anterior
Set-Location ..
