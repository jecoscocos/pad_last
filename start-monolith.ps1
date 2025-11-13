# Скрипт запуска монолитного приложения
# PowerShell script to start monolithic Flask app

Write-Host "🚀 Запуск монолитного приложения..." -ForegroundColor Green
Write-Host ""

# Переход в корневую папку проекта
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "📁 Рабочая папка: $scriptPath" -ForegroundColor Cyan
Write-Host ""

# Проверка Python
Write-Host "🔍 Проверка Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✅ Python найден: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python не найден! Установите Python 3.10+" -ForegroundColor Red
    Write-Host "Скачать: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Проверка виртуального окружения
$venvPath = Join-Path $scriptPath ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "📦 Создание виртуального окружения..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "✅ Виртуальное окружение создано" -ForegroundColor Green
    Write-Host ""
}

# Активация и установка зависимостей
Write-Host "📦 Установка зависимостей..." -ForegroundColor Yellow
& "$venvPath\Scripts\python.exe" -m pip install --upgrade pip --quiet
& "$venvPath\Scripts\pip.exe" install -r requirements.txt --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при установке зависимостей!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Зависимости установлены" -ForegroundColor Green
Write-Host ""

# Запуск приложения
Write-Host "🌐 Запуск Flask приложения..." -ForegroundColor Yellow
Write-Host "Приложение будет доступно по адресу: http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host "Для остановки нажмите Ctrl+C" -ForegroundColor Yellow
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

& "$venvPath\Scripts\python.exe" run.py
