# Servidor HTTP simple para el dashboard
# Soluciona problemas de CORS con archivos locales

Write-Host "Iniciando servidor del dashboard..." -ForegroundColor Green
Write-Host "Carpeta: dashboard/" -ForegroundColor Cyan
Write-Host "URL: http://localhost:8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Presiona Ctrl+C para detener el servidor" -ForegroundColor Red
Write-Host ""

# Navegar a la carpeta dashboard
Set-Location -Path "dashboard"

# Iniciar servidor HTTP en puerto 8000
python -m http.server 8000
