# Test rapido - Solo Caso 1
$API_URL = "http://localhost:8000"

Write-Host "Limpiando datos..." -ForegroundColor Yellow
python limpiar_datos.py

Write-Host "`n[CASO 1] Test de generacion de ruta" -ForegroundColor Cyan

# Crear incidencias
Write-Host "Creando 6 incidencias..." -ForegroundColor Gray
$ids = @()
foreach ($i in 1..6) {
    $tipo = if ($i -in @(1,4)) { "animal_muerto" } else { "zona_critica" }
    $lat = -0.92 - ($i * 0.003)
    $lon = -78.61 + ($i * 0.002)
    
    $body = @{
        tipo = $tipo
        descripcion = "Test $i"
        lat = $lat
        lon = $lon
        usuario_id = 1
    } | ConvertTo-Json -Compress
    
    $resp = Invoke-RestMethod -Uri "$API_URL/api/incidencias/" -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
    $ids += $resp.id
    Write-Host "  Incidencia $($resp.id) creada (tipo=$tipo, gravedad=$($resp.gravedad))" -ForegroundColor Green
}

Write-Host "`nValidando incidencias..." -ForegroundColor Gray
foreach ($id in $ids) {
    Invoke-RestMethod -Uri "$API_URL/api/incidencias/$id/validate" -Method POST | Out-Null
    Write-Host "  Incidencia $id validada" -ForegroundColor Cyan
    Start-Sleep -Milliseconds 500
}

Write-Host "`nVerificando rutas generadas..." -ForegroundColor Gray
$resp = Invoke-RestMethod -Uri "$API_URL/api/rutas/zona/oriental" -Method GET
Write-Host "Respuesta completa:" -ForegroundColor Yellow
$resp | ConvertTo-Json -Depth 3

if ($resp.rutas -and $resp.rutas.Count -gt 0) {
    Write-Host "`n[EXITO] Ruta generada!" -ForegroundColor Green
    Write-Host "  ID: $($resp.rutas[0].id)" -ForegroundColor Cyan
    Write-Host "  Gravedad: $($resp.rutas[0].suma_gravedad)" -ForegroundColor Cyan
    Write-Host "  Camiones: $($resp.rutas[0].camiones_usados)" -ForegroundColor Cyan
} else {
    Write-Host "`n[FALLO] No se genero ruta" -ForegroundColor Red
}
