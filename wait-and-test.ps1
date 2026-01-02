# Script para esperar y probar el health check mejorado
Write-Host "`n🔄 Esperando a que Render complete el despliegue..." -ForegroundColor Cyan
Write-Host "Deploy ID: dep-d5a54o4hg0os73cnimi0`n" -ForegroundColor Gray

$url = "https://epagal-backend-routing-latest.onrender.com/health"
$maxAttempts = 20
$attempt = 0
$waitSeconds = 15

while ($attempt -lt $maxAttempts) {
    $attempt++
    Write-Host "[$attempt/$maxAttempts] Verificando health check..." -ForegroundColor Yellow
    
    try {
        $response = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 10
        
        # Verificar si es la versión nueva (tiene el campo "checks")
        if ($response.checks) {
            Write-Host "`n✅ ¡DEPLOY EXITOSO! Nueva versión detectada`n" -ForegroundColor Green
            Write-Host "📊 Detalles del servicio:" -ForegroundColor Cyan
            Write-Host "   • Estado: $($response.status)" -ForegroundColor White
            Write-Host "   • Servicio: $($response.service)" -ForegroundColor White
            Write-Host "   • Versión: $($response.version)" -ForegroundColor White
            Write-Host "   • Timestamp: $($response.timestamp)" -ForegroundColor White
            Write-Host "   • Ambiente: $($response.environment)" -ForegroundColor White
            Write-Host "   • Python: $($response.python_version)" -ForegroundColor White
            
            Write-Host "`n🔧 Verificaciones:" -ForegroundColor Cyan
            Write-Host "   • Base de datos: $($response.checks.database)" -ForegroundColor White
            Write-Host "   • OSRM Service: $($response.checks.osrm_service)" -ForegroundColor White
            Write-Host "   • API: $($response.checks.api)" -ForegroundColor White
            
            Write-Host "`n🌐 URLs disponibles:" -ForegroundColor Cyan
            Write-Host "   • App: https://epagal-backend-routing-latest.onrender.com" -ForegroundColor White
            Write-Host "   • Docs: https://epagal-backend-routing-latest.onrender.com/docs" -ForegroundColor White
            Write-Host "   • Health: https://epagal-backend-routing-latest.onrender.com/health" -ForegroundColor White
            
            break
        }
        else {
            Write-Host "   ⏳ Versión antigua aún activa, esperando..." -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "   ⚠️  Error al conectar: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    if ($attempt -lt $maxAttempts) {
        Write-Host "   Esperando $waitSeconds segundos...`n" -ForegroundColor Gray
        Start-Sleep -Seconds $waitSeconds
    }
}

if ($attempt -eq $maxAttempts) {
    Write-Host "`n⚠️  El deploy está tomando más tiempo del esperado" -ForegroundColor Yellow
    Write-Host "Verifica el estado en: https://dashboard.render.com/web/srv-d4us303uibrs73f675mg`n" -ForegroundColor White
}
