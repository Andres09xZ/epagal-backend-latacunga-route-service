# Script para detener servicios Docker - Backend EPAGAL Latacunga

Write-Host "🛑 Deteniendo servicios Docker..." -ForegroundColor Cyan

# Verificar si hay contenedores corriendo
$containers = docker-compose ps -q

if ($containers) {
    Write-Host "📋 Contenedores activos encontrados" -ForegroundColor Yellow
    docker-compose ps
    
    Write-Host "`n¿Qué deseas hacer?" -ForegroundColor Cyan
    Write-Host "1) Detener servicios (mantener datos)" -ForegroundColor White
    Write-Host "2) Detener y eliminar volúmenes (eliminar datos)" -ForegroundColor White
    Write-Host "3) Cancelar" -ForegroundColor White
    
    $option = Read-Host "`nSelecciona una opción (1-3)"
    
    switch ($option) {
        "1" {
            Write-Host "`n🛑 Deteniendo servicios..." -ForegroundColor Cyan
            docker-compose down
            Write-Host "✅ Servicios detenidos" -ForegroundColor Green
        }
        "2" {
            Write-Host "`n⚠️  Esto eliminará los volúmenes de datos de RabbitMQ" -ForegroundColor Yellow
            $confirm = Read-Host "¿Estás seguro? (s/n)"
            if ($confirm -eq 's' -or $confirm -eq 'S') {
                Write-Host "`n🛑 Deteniendo servicios y eliminando volúmenes..." -ForegroundColor Cyan
                docker-compose down -v
                Write-Host "✅ Servicios detenidos y volúmenes eliminados" -ForegroundColor Green
            } else {
                Write-Host "❌ Operación cancelada" -ForegroundColor Yellow
            }
        }
        "3" {
            Write-Host "❌ Operación cancelada" -ForegroundColor Yellow
            exit 0
        }
        default {
            Write-Host "❌ Opción inválida" -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host "ℹ️  No hay contenedores activos" -ForegroundColor Yellow
}

Write-Host "`n📊 Estado final:" -ForegroundColor Cyan
docker-compose ps
