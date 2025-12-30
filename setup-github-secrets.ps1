# 🔐 Script para Configurar GitHub Secrets

Write-Host "=================================" -ForegroundColor Cyan
Write-Host "  GitHub Actions - Setup Secrets" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si gh CLI está instalado
$ghInstalled = Get-Command gh -ErrorAction SilentlyContinue

if (-not $ghInstalled) {
    Write-Host "❌ GitHub CLI (gh) no está instalado" -ForegroundColor Red
    Write-Host ""
    Write-Host "📥 Instalación:" -ForegroundColor Yellow
    Write-Host "   1. Descarga desde: https://cli.github.com/" -ForegroundColor White
    Write-Host "   2. O usa winget: winget install --id GitHub.cli" -ForegroundColor White
    Write-Host ""
    Write-Host "🔧 Configuración manual:" -ForegroundColor Yellow
    Write-Host "   1. Ve a: https://github.com/Andres09xZ/epagal-backend-latacunga-route-service/settings/secrets/actions" -ForegroundColor White
    Write-Host "   2. Click en 'New repository secret'" -ForegroundColor White
    Write-Host "   3. Agrega los 3 secrets como se indica en .github/PIPELINE_SETUP.md" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "✅ GitHub CLI detectado" -ForegroundColor Green
Write-Host ""

# Verificar autenticación
Write-Host "🔐 Verificando autenticación con GitHub..." -ForegroundColor Yellow
$authStatus = gh auth status 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ No estás autenticado con GitHub CLI" -ForegroundColor Red
    Write-Host ""
    Write-Host "Ejecuta: gh auth login" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host "✅ Autenticado correctamente" -ForegroundColor Green
Write-Host ""

# Verificar que estamos en el repo correcto
$repoInfo = gh repo view --json nameWithOwner -q .nameWithOwner 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ No estás en un repositorio de GitHub" -ForegroundColor Red
    exit 1
}

Write-Host "📁 Repositorio: $repoInfo" -ForegroundColor Cyan
Write-Host ""

# Función para agregar un secret
function Add-GitHubSecret {
    param(
        [string]$Name,
        [string]$Description,
        [string]$Example
    )
    
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host "🔑 $Name" -ForegroundColor Cyan
    Write-Host "   $Description" -ForegroundColor White
    Write-Host "   Ejemplo: $Example" -ForegroundColor DarkGray
    Write-Host ""
    
    $value = Read-Host "Ingresa el valor (Enter para omitir)"
    
    if ([string]::IsNullOrWhiteSpace($value)) {
        Write-Host "⏭️  Omitido" -ForegroundColor Yellow
        Write-Host ""
        return $false
    }
    
    # Agregar el secret
    $value | gh secret set $Name
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Secret '$Name' configurado" -ForegroundColor Green
        Write-Host ""
        return $true
    } else {
        Write-Host "❌ Error al configurar '$Name'" -ForegroundColor Red
        Write-Host ""
        return $false
    }
}

Write-Host "📋 Configuración de Secrets" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

$secrets = @()

# Secret 1: DOCKER_USERNAME
$result = Add-GitHubSecret `
    -Name "DOCKER_USERNAME" `
    -Description "Usuario de Docker Hub" `
    -Example "mrengineer09"
$secrets += @{Name="DOCKER_USERNAME"; Added=$result}

# Secret 2: DOCKER_PASSWORD
$result = Add-GitHubSecret `
    -Name "DOCKER_PASSWORD" `
    -Description "Contraseña o Access Token de Docker Hub (recomendado: token desde https://hub.docker.com/settings/security)" `
    -Example "dckr_pat_xxxxxxxxxxxxx"
$secrets += @{Name="DOCKER_PASSWORD"; Added=$result}

# Secret 3: RENDER_DEPLOY_HOOK_URL
$result = Add-GitHubSecret `
    -Name "RENDER_DEPLOY_HOOK_URL" `
    -Description "URL del Deploy Hook de Render (Settings > Deploy Hook en tu servicio)" `
    -Example "https://api.render.com/deploy/srv-xxxxx?key=xxxxxx"
$secrets += @{Name="RENDER_DEPLOY_HOOK_URL"; Added=$result}

# Resumen
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "📊 Resumen de Configuración" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

$addedCount = ($secrets | Where-Object { $_.Added }).Count
$totalCount = $secrets.Count

foreach ($secret in $secrets) {
    $status = if ($secret.Added) { "✅" } else { "⏭️" }
    $color = if ($secret.Added) { "Green" } else { "Yellow" }
    Write-Host "$status $($secret.Name)" -ForegroundColor $color
}

Write-Host ""
Write-Host "Total configurados: $addedCount / $totalCount" -ForegroundColor Cyan
Write-Host ""

if ($addedCount -eq $totalCount) {
    Write-Host "🎉 ¡Todos los secrets configurados!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🚀 Siguiente paso:" -ForegroundColor Yellow
    Write-Host "   1. Haz commit y push de los archivos del workflow:" -ForegroundColor White
    Write-Host "      git add .github/" -ForegroundColor DarkGray
    Write-Host "      git commit -m 'ci: Agregar pipeline de GitHub Actions'" -ForegroundColor DarkGray
    Write-Host "      git push origin main" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "   2. Ve a: https://github.com/$repoInfo/actions" -ForegroundColor White
    Write-Host "   3. Verás el pipeline ejecutándose automáticamente" -ForegroundColor White
    Write-Host ""
} elseif ($addedCount -gt 0) {
    Write-Host "⚠️  Algunos secrets no fueron configurados" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Puedes agregarlos manualmente en:" -ForegroundColor White
    Write-Host "https://github.com/$repoInfo/settings/secrets/actions" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host "ℹ️  No se configuraron secrets" -ForegroundColor Blue
    Write-Host ""
    Write-Host "Configúralos manualmente en:" -ForegroundColor White
    Write-Host "https://github.com/$repoInfo/settings/secrets/actions" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "O vuelve a ejecutar este script: .\setup-github-secrets.ps1" -ForegroundColor White
    Write-Host ""
}

Write-Host "📚 Más información en: .github/PIPELINE_SETUP.md" -ForegroundColor Cyan
Write-Host ""
