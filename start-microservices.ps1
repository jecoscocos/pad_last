# Скрипт запуска микросервисов
# PowerShell script to start all 12 microservices

Write-Host "🚀 Запуск микросервисов агентства недвижимости..." -ForegroundColor Green
Write-Host ""

# Переход в папку microservices
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$microservicesPath = Join-Path $scriptPath "microservices"

if (-not (Test-Path $microservicesPath)) {
    Write-Host "❌ Ошибка: папка microservices не найдена!" -ForegroundColor Red
    Write-Host "Текущий путь: $scriptPath" -ForegroundColor Yellow
    exit 1
}

Set-Location $microservicesPath
Write-Host "📁 Рабочая папка: $microservicesPath" -ForegroundColor Cyan
Write-Host ""

# Проверка Docker
Write-Host "🔍 Проверка Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker найден: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker не найден! Установите Docker Desktop." -ForegroundColor Red
    Write-Host "Скачать: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "🐳 Запуск docker-compose..." -ForegroundColor Yellow
Write-Host "Это может занять несколько минут при первом запуске..." -ForegroundColor Cyan
Write-Host ""

# Запуск docker-compose
try {
    docker-compose up --build
} catch {
    Write-Host ""
    Write-Host "❌ Ошибка при запуске docker-compose!" -ForegroundColor Red
    Write-Host "Попробуйте запустить вручную:" -ForegroundColor Yellow
    Write-Host "  cd D:\Lab2Makeev\microservices" -ForegroundColor White
    Write-Host "  docker-compose up --build" -ForegroundColor White
    exit 1
}
