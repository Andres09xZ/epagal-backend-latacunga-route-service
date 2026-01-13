# Script completo para probar generacion automatica de rutas
# Version 2.0 - Con endpoints correctos y verificacion detallada

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
        $resp = Invoke-RestMethod -Uri "$API_URL/api/incidencias/" -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
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
            Write-Host "  [RUTA] Incidencia $Id validada -> Ruta ID=$($resp.ruta_generada.id)" -ForegroundColor Magenta
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

# Funcion para verificar rutas en una zona
function Get-RutasZona($Zona) {
    try {
        $resp = Invoke-RestMethod -Uri "$API_URL/api/rutas/zona/$Zona" -Method GET -ErrorAction Stop
        if ($resp -and $resp.rutas) {
            return @($resp.rutas)
        }
        return @()
    } catch {
        Write-Host "  [DEBUG] Error obteniendo rutas: $_" -ForegroundColor DarkGray
        return @()
    }
}

# ============================================================
# CASO 1: Generar Ruta 1 (Norte Oriental)
# ============================================================
Write-Host ""
Write-Host "[CASO 1] Generacion de Ruta 1 (Norte Oriental)" -ForegroundColor Yellow
Write-Host "Objetivo: Superar umbral (22 puntos) y generar primera ruta" -ForegroundColor Gray
Write-Host "Creando 6 incidencias en el norte..." -ForegroundColor Gray

$ids1 = @()
$ids1 += New-Incidencia "animal_muerto" -0.9200 -78.6100 "Animal muerto - Norte 1"
$ids1 += New-Incidencia "zona_critica" -0.9250 -78.6120 "Zona critica - Norte 2"
$ids1 += New-Incidencia "zona_critica" -0.9280 -78.6150 "Zona critica - Norte 3"
$ids1 += New-Incidencia "animal_muerto" -0.9300 -78.6080 "Animal muerto - Norte 4"
$ids1 += New-Incidencia "zona_critica" -0.9320 -78.6140 "Zona critica - Norte 5"
$ids1 += New-Incidencia "zona_critica" -0.9330 -78.6160 "Zona critica - Norte 6"

Write-Host ""
Write-Host "Validando incidencias (esperando generacion en la 6ta)..." -ForegroundColor Gray
$rutaGenerada1 = $false
foreach ($id in $ids1) {
    if ($id) {
        Start-Sleep -Milliseconds 500
        if (Validate-Incidencia $id) {
            $rutaGenerada1 = $true
        }
    }
}

Write-Host ""
Write-Host "Verificando rutas en zona oriental..." -ForegroundColor Gray
$rutasOrientales = Get-RutasZona "oriental"
Write-Host "  [DEBUG] Rutas recibidas: $($rutasOrientales.Count)" -ForegroundColor DarkGray
$caso1Pass = ($rutasOrientales.Count -ge 1)

if ($caso1Pass) {
    Write-Host "[PASS] Caso 1: Ruta generada exitosamente" -ForegroundColor Green
    Write-Host "  -> Ruta ID: $($rutasOrientales[0].id)" -ForegroundColor Cyan
    Write-Host "  -> Gravedad: $($rutasOrientales[0].suma_gravedad)" -ForegroundColor Cyan
    Write-Host "  -> Camiones: $($rutasOrientales[0].camiones_usados)" -ForegroundColor Cyan
} else {
    Write-Host "[FAIL] Caso 1: No se genero la ruta" -ForegroundColor Red
    Write-Host "  -> Rutas encontradas: $($rutasOrientales.Count)" -ForegroundColor Red
}

Read-Host "`nPresiona Enter para continuar al Caso 2"

# ============================================================
# CASO 2: Probar anti-solapamiento
# ============================================================
Write-Host ""
Write-Host "[CASO 2] Logica Anti-Solapamiento" -ForegroundColor Yellow
Write-Host "Objetivo: Incidencias CERCA de Ruta 1 NO deben generar nueva ruta" -ForegroundColor Gray
Write-Host "Creando 3 incidencias CERCA de la Ruta 1 (< 500m)..." -ForegroundColor Gray

$ids2 = @()
$ids2 += New-Incidencia "acopio" -0.9210 -78.6110 "Acopio cerca Norte 1"
$ids2 += New-Incidencia "zona_critica" -0.9260 -78.6130 "Zona critica cerca Norte 2"
$ids2 += New-Incidencia "acopio" -0.9290 -78.6090 "Acopio cerca Norte 4"

Write-Host ""
Write-Host "Validando incidencias cercanas..." -ForegroundColor Gray
foreach ($id in $ids2) {
    if ($id) {
        Start-Sleep -Milliseconds 500
        Validate-Incidencia $id | Out-Null
    }
}

Write-Host ""
Write-Host "Verificando que NO se haya generado nueva ruta..." -ForegroundColor Gray
$rutasOrientales2 = Get-RutasZona "oriental"
$caso2Pass = ($rutasOrientales2.Count -eq 1)  # Debe seguir siendo 1

if ($caso2Pass) {
    Write-Host "[PASS] Caso 2: Anti-solapamiento funciono" -ForegroundColor Green
    Write-Host "  -> Rutas en zona oriental: $($rutasOrientales2.Count) (sin cambios)" -ForegroundColor Cyan
} else {
    Write-Host "[FAIL] Caso 2: Se genero ruta cuando NO debia" -ForegroundColor Red
    Write-Host "  -> Rutas en zona oriental: $($rutasOrientales2.Count) (deberia ser 1)" -ForegroundColor Red
}

Read-Host "`nPresiona Enter para continuar al Caso 3"

# ============================================================
# CASO 3: Generar Ruta 2 (Sur Oriental - Lejos de Ruta 1)
# ============================================================
Write-Host ""
Write-Host "[CASO 3] Generacion de Ruta 2 (Sur Oriental)" -ForegroundColor Yellow
Write-Host "Objetivo: Incidencias LEJOS de Ruta 1 (> 500m) generan nueva ruta" -ForegroundColor Gray
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
foreach ($id in $ids3) {
    if ($id) {
        Start-Sleep -Milliseconds 500
        Validate-Incidencia $id | Out-Null
    }
}

Write-Host ""
Write-Host "Verificando que se haya generado Ruta 2..." -ForegroundColor Gray
$rutasOrientales3 = Get-RutasZona "oriental"
$caso3Pass = ($rutasOrientales3.Count -eq 2)  # Ahora deben ser 2

if ($caso3Pass) {
    Write-Host "[PASS] Caso 3: Ruta 2 generada exitosamente" -ForegroundColor Green
    Write-Host "  -> Total de rutas orientales: $($rutasOrientales3.Count)" -ForegroundColor Cyan
    Write-Host "  -> Ruta 1 ID: $($rutasOrientales3[0].id), Gravedad: $($rutasOrientales3[0].suma_gravedad)" -ForegroundColor Cyan
    Write-Host "  -> Ruta 2 ID: $($rutasOrientales3[1].id), Gravedad: $($rutasOrientales3[1].suma_gravedad)" -ForegroundColor Cyan
} else {
    Write-Host "[FAIL] Caso 3: No se genero Ruta 2" -ForegroundColor Red
    Write-Host "  -> Rutas en zona oriental: $($rutasOrientales3.Count) (deberia ser 2)" -ForegroundColor Red
}

Read-Host "`nPresiona Enter para continuar al Caso 4"

# ============================================================
# CASO 4: Generar Ruta 3 (Zona Occidental)
# ============================================================
Write-Host ""
Write-Host "[CASO 4] Generacion de Ruta 3 (Zona Occidental)" -ForegroundColor Yellow
Write-Host "Objetivo: Validar que cada zona tiene su propio umbral" -ForegroundColor Gray
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
foreach ($id in $ids4) {
    if ($id) {
        Start-Sleep -Milliseconds 500
        Validate-Incidencia $id | Out-Null
    }
}

Write-Host ""
Write-Host "Verificando rutas en zona occidental..." -ForegroundColor Gray
$rutasOccidentales = Get-RutasZona "occidental"
$caso4Pass = ($rutasOccidentales.Count -eq 1)

if ($caso4Pass) {
    Write-Host "[PASS] Caso 4: Ruta 3 generada exitosamente" -ForegroundColor Green
    Write-Host "  -> Ruta ID: $($rutasOccidentales[0].id)" -ForegroundColor Cyan
    Write-Host "  -> Gravedad: $($rutasOccidentales[0].suma_gravedad)" -ForegroundColor Cyan
    Write-Host "  -> Camiones: $($rutasOccidentales[0].camiones_usados)" -ForegroundColor Cyan
} else {
    Write-Host "[FAIL] Caso 4: No se genero Ruta 3" -ForegroundColor Red
    Write-Host "  -> Rutas en zona occidental: $($rutasOccidentales.Count) (deberia ser 1)" -ForegroundColor Red
}

# ============================================================
# RESUMEN FINAL
# ============================================================
Write-Host ""
Write-Host "========================================"
Write-Host "RESUMEN DE PRUEBAS"
Write-Host "========================================"
Write-Host ""

$totalPass = 0
if ($caso1Pass) { $totalPass++ }
if ($caso2Pass) { $totalPass++ }
if ($caso3Pass) { $totalPass++ }
if ($caso4Pass) { $totalPass++ }

Write-Host "Resultados:" -ForegroundColor White
Write-Host "  Caso 1 (Ruta 1 Oriental Norte): $(if($caso1Pass){'PASS'}else{'FAIL'})" -ForegroundColor $(if($caso1Pass){'Green'}else{'Red'})
Write-Host "  Caso 2 (Anti-solapamiento):     $(if($caso2Pass){'PASS'}else{'FAIL'})" -ForegroundColor $(if($caso2Pass){'Green'}else{'Red'})
Write-Host "  Caso 3 (Ruta 2 Oriental Sur):   $(if($caso3Pass){'PASS'}else{'FAIL'})" -ForegroundColor $(if($caso3Pass){'Green'}else{'Red'})
Write-Host "  Caso 4 (Ruta 3 Occidental):     $(if($caso4Pass){'PASS'}else{'FAIL'})" -ForegroundColor $(if($caso4Pass){'Green'}else{'Red'})

Write-Host ""
Write-Host "TOTAL: $totalPass/4 casos exitosos" -ForegroundColor $(if($totalPass -eq 4){'Green'}else{'Yellow'})

Write-Host ""
Write-Host "Estadisticas finales:" -ForegroundColor White
Write-Host "  - Rutas en zona oriental: $($rutasOrientales3.Count)" -ForegroundColor Cyan
Write-Host "  - Rutas en zona occidental: $($rutasOccidentales.Count)" -ForegroundColor Cyan
Write-Host "  - Total de rutas generadas: $($rutasOrientales3.Count + $rutasOccidentales.Count)" -ForegroundColor Cyan

Write-Host ""
Write-Host "Dashboard: http://localhost:8080" -ForegroundColor Yellow
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host ""
