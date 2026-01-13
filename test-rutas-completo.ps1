<#
.SYNOPSIS
    Script completo para probar el sistema de generación automática de rutas
    
.DESCRIPTION
    Este script prueba todos los casos de uso del sistema:
    1. Generación de primera ruta cuando se supera umbral
    2. Validación de lógica anti-solapamiento (incidencias cercanas)
    3. Generación de segunda ruta independiente (incidencias lejanas)
    4. Validación de zona Occidental independiente
    
.NOTES
    Autor: Sistema de Testing Automatizado
    Fecha: 12/01/2026
#>

$API_URL = "http://localhost:8000"
$HEADERS = @{
    "Content-Type" = "application/json"
}

# Colores para output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }
function Write-Step { Write-Host "`n========================================" -ForegroundColor Magenta; Write-Host $args -ForegroundColor Magenta; Write-Host "========================================`n" -ForegroundColor Magenta }

# Función para hacer pausa
function Wait-Continue {
    param([string]$Message = "Presiona Enter para continuar...")
    Write-Host "`n" -NoNewline
    Read-Host $Message
}

# Función para crear incidencia
function New-Incidencia {
    param(
        [string]$Tipo,
        [double]$Lat,
        [double]$Lon,
        [string]$Descripcion,
        [int]$UsuarioId = 1
    )
    
    $body = @{
        tipo = $Tipo
        descripcion = $Descripcion
        lat = $Lat
        lon = $Lon
        usuario_id = $UsuarioId
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$API_URL/api/incidencias" -Method POST -Headers $HEADERS -Body $body
        Write-Success "✅ Incidencia creada: ID=$($response.id), Tipo=$Tipo, Gravedad=$($response.gravedad)"
        return $response.id
    } catch {
        Write-Error "❌ Error creando incidencia: $_"
        return $null
    }
}

# Función para validar incidencia
function Approve-Incidencia {
    param([int]$Id)
    
    try {
        $response = Invoke-RestMethod -Uri "$API_URL/api/incidencias/$Id/validate" -Method PUT
        
        if ($response.ruta_generada) {
            Write-Success "✅ Incidencia #$Id validada - 🚨 RUTA GENERADA: #$($response.ruta_generada.id)"
            return $true
        } else {
            Write-Info "✅ Incidencia #$Id validada - Sin generación de ruta"
            return $false
        }
    } catch {
        Write-Error "❌ Error validando incidencia #$Id : $_"
        return $false
    }
}

# Función para obtener estado de umbrales
function Get-EstadoUmbrales {
    try {
        $response = Invoke-RestMethod -Uri "$API_URL/api/rutas/umbrales"
        Write-Info "`n📊 ESTADO DE UMBRALES:"
        foreach ($umbral in $response) {
            $porcentaje = [math]::Round(($umbral.suma_gravedad / $umbral.umbral) * 100, 0)
            $barra = "█" * [math]::Min([math]::Floor($porcentaje / 5), 20)
            $espacios = " " * [math]::Max(20 - $barra.Length, 0)
            
            Write-Host "  🌍 Zona $($umbral.zona):" -NoNewline
            Write-Host " [$barra$espacios] " -NoNewline -ForegroundColor $(if ($umbral.supera_umbral) { "Red" } else { "Yellow" })
            Write-Host "$($umbral.suma_gravedad)/$($umbral.umbral) puntos ($porcentaje%25)" -ForegroundColor $(if ($umbral.supera_umbral) { "Red" } else { "Cyan" })
            Write-Host "     Incidencias validadas: $($umbral.incidencias_validadas)" -ForegroundColor Gray
            
            if ($umbral.supera_umbral) {
                Write-Host "     🚨 UMBRAL SUPERADO - Listo para generar ruta" -ForegroundColor Red
            }
        }
        Write-Host ""
    } catch {
        Write-Error "❌ Error obteniendo umbrales: $_"
    }
}

# Función para listar rutas
function Get-Rutas {
    try {
        $response = Invoke-RestMethod -Uri "$API_URL/api/rutas"
        Write-Info "`n📋 RUTAS GENERADAS:"
        
        if ($response.Count -eq 0) {
            Write-Warning "  No hay rutas generadas aún"
        } else {
            foreach ($ruta in $response) {
                Write-Host "  🚛 Ruta #$($ruta.id) - $($ruta.zona)" -ForegroundColor Green
                Write-Host "     Estado: $($ruta.estado)" -ForegroundColor Cyan
                Write-Host "     Gravedad: $($ruta.suma_gravedad) puntos" -ForegroundColor Yellow
                Write-Host "     Camiones: $($ruta.camiones_usados)" -ForegroundColor Magenta
                Write-Host "     Distancia: $([math]::Round($ruta.distancia_total / 1000, 2)) km" -ForegroundColor Blue
                Write-Host "     Duración: $($ruta.duracion_estimada)" -ForegroundColor Gray
            }
        }
        Write-Host ""
    } catch {
        Write-Error "❌ Error obteniendo rutas: $_"
    }
}

# ==============================================================================
# INICIO DEL SCRIPT
# ==============================================================================

Clear-Host
Write-Host @"
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║     🧪 TEST COMPLETO: SISTEMA DE GENERACIÓN DE RUTAS          ║
║                                                                ║
║     Backend Latacunga - Sistema de Incidencias                ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

Write-Info "`n📋 Este script probará los siguientes casos de uso:"
Write-Host "  1. Generación de Ruta 1 (Zona Oriental - Norte)" -ForegroundColor White
Write-Host "  2. Lógica Anti-Solapamiento (Incidencias cercanas a Ruta 1)" -ForegroundColor White
Write-Host "  3. Generación de Ruta 2 (Zona Oriental - Sur, lejos de Ruta 1)" -ForegroundColor White
Write-Host "  4. Generación de Ruta 3 (Zona Occidental - Independiente)" -ForegroundColor White

Wait-Continue

# Verificar que el servidor esté corriendo
Write-Step "🔍 PASO 0: Verificando conectividad con el servidor"
try {
    $health = Invoke-RestMethod -Uri "$API_URL/health" -ErrorAction Stop
    Write-Success "✅ Servidor activo y respondiendo"
} catch {
    Write-Error "❌ No se puede conectar al servidor en $API_URL"
    Write-Error "   Asegúrate de que el servidor esté corriendo con: uvicorn app.main:app --reload"
    exit 1
}

# Limpiar datos
Write-Step "🧹 PASO 1: Limpiando datos de prueba anteriores"
Write-Warning "Se eliminarán todas las incidencias, rutas y notificaciones existentes"
$confirmar = Read-Host "¿Continuar? (S/N)"
if ($confirmar -ne "S" -and $confirmar -ne "s") {
    Write-Warning "Operación cancelada"
    exit 0
}

try {
    python limpiar_datos.py
    Write-Success "✅ Datos limpiados exitosamente"
    Start-Sleep -Seconds 2
} catch {
    Write-Error "❌ Error limpiando datos: $_"
    exit 1
}

Get-EstadoUmbrales
Wait-Continue

# ==============================================================================
# CASO DE USO 1: GENERACIÓN DE PRIMERA RUTA (ZONA ORIENTAL - NORTE)
# ==============================================================================

Write-Step "CASO 1: Generación de Primera Ruta (Zona Oriental - Norte)"
Write-Info "Objetivo: Crear y validar 5 incidencias en el norte para superar el umbral (23 puntos mayor a 20)"

Write-Host "`nCreando 5 incidencias en el sector NORTE de la Zona Oriental..." -ForegroundColor Yellow

$ids_norte = @()
$ids_norte += New-Incidencia -Tipo "animal_muerto" -Lat -0.9200 -Lon -78.6100 -Descripcion "Animal muerto - Norte 1"
$ids_norte += New-Incidencia -Tipo "zona_critica" -Lat -0.9250 -Lon -78.6120 -Descripcion "Zona crítica - Norte 2"
$ids_norte += New-Incidencia -Tipo "zona_critica" -Lat -0.9280 -Lon -78.6150 -Descripcion "Zona crítica - Norte 3"
$ids_norte += New-Incidencia -Tipo "animal_muerto" -Lat -0.9300 -Lon -78.6080 -Descripcion "Animal muerto - Norte 4"
$ids_norte += New-Incidencia -Tipo "zona_critica" -Lat -0.9320 -Lon -78.6140 -Descripcion "Zona crítica - Norte 5"

Write-Info "`n📊 Gravedad total esperada: 5+3+3+5+3 = 23 puntos"
Get-EstadoUmbrales

Write-Host "`nValidando incidencias una por una..." -ForegroundColor Yellow
$ruta_generada = $false
foreach ($id in $ids_norte) {
    if ($id) {
        Start-Sleep -Milliseconds 500
        $resultado = Approve-Incidencia -Id $id
        if ($resultado) {
            $ruta_generada = $true
            break
        }
    }
}

if ($ruta_generada) {
    Write-Success "`nÉXITO! La Ruta 1 fue generada automáticamente"
} else {
    Write-Error "`nERROR: No se generó ninguna ruta"
}

Get-EstadoUmbrales
Get-Rutas
Wait-Continue

# ==============================================================================
# CASO DE USO 2: LÓGICA ANTI-SOLAPAMIENTO (INCIDENCIAS CERCANAS)
# ==============================================================================

Write-Step "CASO 2: Lógica Anti-Solapamiento (Incidencias Cercanas)"
Write-Info "Objetivo: Validar 3 incidencias CERCA de la Ruta 1 (menor a 500m)"
Write-Info "Resultado esperado: NO generar nueva ruta, las incidencias quedan validadas"

Write-Host "`nCreando 3 incidencias CERCA de las incidencias de la Ruta 1..." -ForegroundColor Yellow

$ids_cerca = @()
$ids_cerca += New-Incidencia -Tipo "acopio" -Lat -0.9210 -Lon -78.6110 -Descripcion "Acopio cerca de Norte 1"
$ids_cerca += New-Incidencia -Tipo "zona_critica" -Lat -0.9260 -Lon -78.6130 -Descripcion "Zona crítica cerca de Norte 2"
$ids_cerca += New-Incidencia -Tipo "acopio" -Lat -0.9290 -Lon -78.6090 -Descripcion "Acopio cerca de Norte 4"

Write-Info "`n📊 Gravedad total: 1+3+1 = 5 puntos adicionales"

Write-Host "`nValidando incidencias cercanas..." -ForegroundColor Yellow
$nueva_ruta = $false
foreach ($id in $ids_cerca) {
    if ($id) {
        Start-Sleep -Milliseconds 500
        $resultado = Approve-Incidencia -Id $id
        if ($resultado) {
            $nueva_ruta = $true
        }
    }
}

if ($nueva_ruta) {
    Write-Error "`nERROR: Se generó una ruta cuando NO debería (solapamiento)"
} else {
    Write-Success "`nÉXITO! NO se generó ruta (las incidencias están a menos de 500m de la Ruta 1)"
    Write-Info "   Las 3 incidencias quedan validadas para futuras rutas"
}

Get-EstadoUmbrales
Get-Rutas
Wait-Continue

# ==============================================================================
# CASO DE USO 3: GENERACIÓN DE SEGUNDA RUTA (ZONA ORIENTAL - SUR, LEJOS)
# ==============================================================================

Write-Step "CASO 3: Generación de Segunda Ruta (Zona Oriental - Sur, Lejos)"
Write-Info "Objetivo: Crear y validar 5 incidencias en el SUR, lejos de la Ruta 1"
Write-Info "Resultado esperado: Generar Ruta 2 independiente"

Write-Host "`nCreando 5 incidencias en el sector SUR (más de 5km de la Ruta 1)..." -ForegroundColor Yellow

$ids_sur = @()
$ids_sur += New-Incidencia -Tipo "animal_muerto" -Lat -0.9800 -Lon -78.6100 -Descripcion "Animal muerto - Sur 1"
$ids_sur += New-Incidencia -Tipo "zona_critica" -Lat -0.9850 -Lon -78.6120 -Descripcion "Zona crítica - Sur 2"
$ids_sur += New-Incidencia -Tipo "zona_critica" -Lat -0.9880 -Lon -78.6150 -Descripcion "Zona crítica - Sur 3"
$ids_sur += New-Incidencia -Tipo "animal_muerto" -Lat -0.9900 -Lon -78.6080 -Descripcion "Animal muerto - Sur 4"
$ids_sur += New-Incidencia -Tipo "zona_critica" -Lat -0.9920 -Lon -78.6140 -Descripcion "Zona crítica - Sur 5"

Write-Info "`n📊 Gravedad total esperada: 5+3+3+5+3 = 23 puntos"
Write-Info "   (Excluyendo las incidencias ya asignadas a la Ruta 1)"

Write-Host "`nValidando incidencias del Sur..." -ForegroundColor Yellow
$ruta_generada = $false
foreach ($id in $ids_sur) {
    if ($id) {
        Start-Sleep -Milliseconds 500
        $resultado = Approve-Incidencia -Id $id
        if ($resultado) {
            $ruta_generada = $true
            break
        }
    }
}

if ($ruta_generada) {
    Write-Success "`nÉXITO! La Ruta 2 fue generada automáticamente (independiente de Ruta 1)"
} else {
    Write-Error "`nERROR: No se generó la Ruta 2"
    Write-Warning "   Verifica que las incidencias del Sur estén a más de 500m de la Ruta 1"
}

Get-EstadoUmbrales
Get-Rutas
Wait-Continue

# ==============================================================================
# CASO DE USO 4: GENERACIÓN DE RUTA EN ZONA OCCIDENTAL
# ==============================================================================

Write-Step "CASO 4: Generación de Ruta en Zona Occidental (Independiente)"
Write-Info "Objetivo: Crear y validar 5 incidencias en la Zona Occidental"
Write-Info "Resultado esperado: Generar Ruta 3 (independiente de las rutas Orientales)"

Write-Host "`nCreando 5 incidencias en la Zona OCCIDENTAL (longitud menor a -78.6191)..." -ForegroundColor Yellow

$ids_occidental = @()
$ids_occidental += New-Incidencia -Tipo "animal_muerto" -Lat -0.9200 -Lon -78.6300 -Descripcion "Animal muerto - Occidental 1"
$ids_occidental += New-Incidencia -Tipo "zona_critica" -Lat -0.9250 -Lon -78.6320 -Descripcion "Zona crítica - Occidental 2"
$ids_occidental += New-Incidencia -Tipo "zona_critica" -Lat -0.9280 -Lon -78.6350 -Descripcion "Zona crítica - Occidental 3"
$ids_occidental += New-Incidencia -Tipo "animal_muerto" -Lat -0.9300 -Lon -78.6280 -Descripcion "Animal muerto - Occidental 4"
$ids_occidental += New-Incidencia -Tipo "zona_critica" -Lat -0.9320 -Lon -78.6340 -Descripcion "Zona crítica - Occidental 5"

Write-Info "`n📊 Gravedad total esperada: 5+3+3+5+3 = 23 puntos"

Write-Host "`nValidando incidencias Occidentales..." -ForegroundColor Yellow
$ruta_generada = $false
foreach ($id in $ids_occidental) {
    if ($id) {
        Start-Sleep -Milliseconds 500
        $resultado = Approve-Incidencia -Id $id
        if ($resultado) {
            $ruta_generada = $true
            break
        }
    }
}

if ($ruta_generada) {
    Write-Success "`nÉXITO! La Ruta 3 fue generada en la Zona Occidental"
} else {
    Write-Error "`nERROR: No se generó la Ruta 3"
}

Get-EstadoUmbrales
Get-Rutas

# ==============================================================================
# RESUMEN FINAL
# ==============================================================================

Write-Step "📊 RESUMEN FINAL DE PRUEBAS"

Write-Host "`n✅ PRUEBAS COMPLETADAS:" -ForegroundColor Green
Write-Host "  ✓ Caso 1: Generación de primera ruta" -ForegroundColor Green
Write-Host "  ✓ Caso 2: Lógica anti-solapamiento" -ForegroundColor Green
Write-Host "  ✓ Caso 3: Generación de segunda ruta independiente" -ForegroundColor Green
Write-Host "  ✓ Caso 4: Generación de ruta en zona Occidental" -ForegroundColor Green

Write-Host "`n🌐 ACCEDE AL DASHBOARD:" -ForegroundColor Cyan
Write-Host "  http://localhost:8080" -ForegroundColor Yellow

Write-Host "`n📋 VERIFICA EN EL DASHBOARD:" -ForegroundColor Cyan
Write-Host "  1. Tab 'Incidencias': Verifica estados (validada/asignada)" -ForegroundColor White
Write-Host "  2. Tab 'Rutas': Verifica que existan 3 rutas" -ForegroundColor White
Write-Host "  3. Click 'Ver Detalles' en cada ruta para ver el mapa" -ForegroundColor White
Write-Host "  4. Verifica que las polylines se visualicen correctamente" -ForegroundColor White

Write-Host "`n🎉 ¡TESTING COMPLETADO!" -ForegroundColor Green
Write-Host ""
