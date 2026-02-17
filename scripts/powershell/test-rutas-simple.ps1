# Script para probar generacion automatica de rutas
# Sin emojis para evitar problemas de encoding

$API_URL = "http://localhost:8000"

Write-Host ""
Write-Host "========================================"
Write-Host "TEST: SISTEMA DE GENERACION DE RUTAS"
Write-Host "========================================"
Write-Host ""

# Verificar servidor
try {
    Invoke-RestMethod -Uri "$API_URL/health" -ErrorAction Stop | Out-Null
    Write-Host "[OK] Servidor activo" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "[ERROR] No se puede conectar al servidor" -ForegroundColor Red
    exit 1
}

# Limpiar datos
Write-Host "Limpiando datos anteriores..." -ForegroundColor Yellow
python limpiar_datos.py
Write-Host ""

# Funcion para crear incidencia
function New-Incidencia($Tipo, $Lat, $Lon, $Desc) {
    $body = @{
        tipo = $Tipo
        descripcion = $Desc
        lat = $Lat
        lon = $Lon
        usuario_id = 1
    } | ConvertTo-Json -Compress
    
    try {
        $resp = Invoke-RestMethod -Uri "$API_URL/api/incidencias" -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
        Write-Host "  [+] Incidencia creada: ID=$($resp.id), Tipo=$Tipo, Gravedad=$($resp.gravedad)" -ForegroundColor Green
        return $resp.id
    } catch {
        Write-Host "  [ERROR] No se pudo crear incidencia" -ForegroundColor Red
        return $null
    }
}

# Funcion para validar incidencia
function Validate-Incidencia($Id) {
    try {
        $resp = Invoke-RestMethod -Uri "$API_URL/api/incidencias/$Id/validate" -Method POST
        if ($resp.ruta_generada) {
            Write-Host "  [RUTA GENERADA] Incidencia $Id validada -> Ruta ID=$($resp.ruta_generada.id)" -ForegroundColor Magenta
            return $true
        } else {
            Write-Host "  [OK] Incidencia $Id validada" -ForegroundColor Cyan
            return $false
        }
    } catch {
        Write-Host "  [ERROR] Error validando incidencia $Id" -ForegroundColor Red
        return $false
    }
}

# CASO 1: Generar Ruta 1 (Norte Oriental)
Write-Host ""
Write-Host "[CASO 1] Generacion de Ruta 1 (Norte Oriental)" -ForegroundColor Yellow
Write-Host "Creando 6 incidencias en el norte..." -ForegroundColor Gray

$ids1 = @()
$ids1 += New-Incidencia "animal_muerto" -0.9200 -78.6100 "Animal muerto - Norte 1"
$ids1 += New-Incidencia "zona_critica" -0.9250 -78.6120 "Zona critica - Norte 2"
$ids1 += New-Incidencia "zona_critica" -0.9280 -78.6150 "Zona critica - Norte 3"
$ids1 += New-Incidencia "animal_muerto" -0.9300 -78.6080 "Animal muerto - Norte 4"
$ids1 += New-Incidencia "zona_critica" -0.9320 -78.6140 "Zona critica - Norte 5"
$ids1 += New-Incidencia "zona_critica" -0.9330 -78.6160 "Zona critica - Norte 6"

Write-Host ""
Write-Host "Validando incidencias..." -ForegroundColor Gray
$ruta1 = $false
foreach ($id in $ids1) {
    if ($id) {
        Start-Sleep -Milliseconds 300
        if (Validate-Incidencia $id) {
            $ruta1 = $true
        }
    }
}

if ($ruta1) {
    Write-Host ""
    Write-Host "[EXITO] Ruta 1 generada!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[FALLO] No se genero Ruta 1" -ForegroundColor Red
}

Read-Host "Presiona Enter para continuar"

# CASO 2: Probar anti-solapamiento
Write-Host ""
Write-Host "[CASO 2] Logica Anti-Solapamiento" -ForegroundColor Yellow
Write-Host "Creando 3 incidencias CERCA de la Ruta 1..." -ForegroundColor Gray

$ids2 = @()
$ids2 += New-Incidencia "acopio" -0.9210 -78.6110 "Acopio cerca Norte 1"
$ids2 += New-Incidencia "zona_critica" -0.9260 -78.6130 "Zona critica cerca Norte 2"
$ids2 += New-Incidencia "acopio" -0.9290 -78.6090 "Acopio cerca Norte 4"

Write-Host ""
Write-Host "Validando incidencias cercanas..." -ForegroundColor Gray
$rutaNueva = $false
foreach ($id in $ids2) {
    if ($id) {
        Start-Sleep -Milliseconds 300
        if (Validate-Incidencia $id) {
            $rutaNueva = $true
        }
    }
}

if ($rutaNueva) {
    Write-Host ""
    Write-Host "[FALLO] Se genero ruta cuando NO deberia (solapamiento)" -ForegroundColor Red
} else {
    Write-Host ""
    Write-Host "[EXITO] NO se genero ruta (anti-solapamiento funciono)" -ForegroundColor Green
}

Read-Host "Presiona Enter para continuar"

# CASO 3: Generar Ruta 2 (Sur Oriental)
Write-Host ""
Write-Host "[CASO 3] Generacion de Ruta 2 (Sur Oriental)" -ForegroundColor Yellow
Write-Host "Creando 6 incidencias en el sur (lejos de Ruta 1)..." -ForegroundColor Gray

$ids3 = @()
$ids3 += New-Incidencia "animal_muerto" -0.9800 -78.6100 "Animal muerto - Sur 1"
$ids3 += New-Incidencia "zona_critica" -0.9850 -78.6120 "Zona critica - Sur 2"
$ids3 += New-Incidencia "zona_critica" -0.9880 -78.6150 "Zona critica - Sur 3"
$ids3 += New-Incidencia "animal_muerto" -0.9900 -78.6080 "Animal muerto - Sur 4"
$ids3 += New-Incidencia "zona_critica" -0.9920 -78.6140 "Zona critica - Sur 5"
$ids3 += New-Incidencia "zona_critica" -0.9930 -78.6160 "Zona critica - Sur 6"

Write-Host ""
Write-Host "Validando incidencias del sur..." -ForegroundColor Gray
$ruta2 = $false
foreach ($id in $ids3) {
    if ($id) {
        Start-Sleep -Milliseconds 300
        if (Validate-Incidencia $id) {
            $ruta2 = $true
        }
    }
}

if ($ruta2) {
    Write-Host ""
    Write-Host "[EXITO] Ruta 2 generada (independiente de Ruta 1)!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[FALLO] No se genero Ruta 2" -ForegroundColor Red
}

Read-Host "Presiona Enter para continuar"

# CASO 4: Generar Ruta 3 (Occidental)
Write-Host ""
Write-Host "[CASO 4] Generacion de Ruta 3 (Zona Occidental)" -ForegroundColor Yellow
Write-Host "Creando 6 incidencias en zona occidental..." -ForegroundColor Gray

$ids4 = @()
$ids4 += New-Incidencia "animal_muerto" -0.9200 -78.6300 "Animal muerto - Occidental 1"
$ids4 += New-Incidencia "zona_critica" -0.9250 -78.6320 "Zona critica - Occidental 2"
$ids4 += New-Incidencia "zona_critica" -0.9280 -78.6350 "Zona critica - Occidental 3"
$ids4 += New-Incidencia "animal_muerto" -0.9300 -78.6280 "Animal muerto - Occidental 4"
$ids4 += New-Incidencia "zona_critica" -0.9320 -78.6340 "Zona critica - Occidental 5"
$ids4 += New-Incidencia "zona_critica" -0.9330 -78.6360 "Zona critica - Occidental 6"

Write-Host ""
Write-Host "Validando incidencias occidentales..." -ForegroundColor Gray
$ruta3 = $false
foreach ($id in $ids4) {
    if ($id) {
        Start-Sleep -Milliseconds 300
        if (Validate-Incidencia $id) {
            $ruta3 = $true
        }
    }
}

if ($ruta3) {
    Write-Host ""
    Write-Host "[EXITO] Ruta 3 generada!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[FALLO] No se genero Ruta 3" -ForegroundColor Red
}

# RESUMEN
Write-Host ""
Write-Host "========================================"
Write-Host "RESUMEN DE PRUEBAS"
Write-Host "========================================"
Write-Host ""

Write-Host "Resultados:" -ForegroundColor White
Write-Host "  Caso 1 (Ruta 1): $(if($ruta1){'PASS'}else{'FAIL'})" -ForegroundColor $(if($ruta1){'Green'}else{'Red'})
Write-Host "  Caso 2 (Anti-solapamiento): $(if(-not$rutaNueva){'PASS'}else{'FAIL'})" -ForegroundColor $(if(-not$rutaNueva){'Green'}else{'Red'})
Write-Host "  Caso 3 (Ruta 2): $(if($ruta2){'PASS'}else{'FAIL'})" -ForegroundColor $(if($ruta2){'Green'}else{'Red'})
Write-Host "  Caso 4 (Ruta 3): $(if($ruta3){'PASS'}else{'FAIL'})" -ForegroundColor $(if($ruta3){'Green'}else{'Red'})

Write-Host ""
Write-Host "Accede al dashboard: http://localhost:8080" -ForegroundColor Yellow
Write-Host ""
