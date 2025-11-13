# Скрипт для запуска всех тестов микросервисов
# Использование: .\run-all-tests.ps1

Write-Host "🧪 Запуск всех тестов микросервисов..." -ForegroundColor Cyan
Write-Host ""

$services = @(
    "auth-service",
    "property-service",
    "notification-service",
    "analytics-service"
)

$totalTests = 0
$passedTests = 0
$failedTests = 0
$results = @()

foreach ($service in $services) {
    $servicePath = Join-Path "microservices" $service
    $testFile = Join-Path $servicePath "test_$($service -replace '-service','').py"
    
    if (Test-Path $testFile) {
        Write-Host "📦 Тестирование: $service" -ForegroundColor Yellow
        Write-Host "   Файл: $testFile"
        
        Push-Location $servicePath
        
        # Запуск pytest с выводом в JSON
        $output = python -m pytest "test_*.py" -v --tb=short --json-report --json-report-file=report.json 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Успешно" -ForegroundColor Green
            $passedTests++
            $results += [PSCustomObject]@{
                Service = $service
                Status = "PASSED"
                Color = "Green"
            }
        } else {
            Write-Host "   ❌ Провалено" -ForegroundColor Red
            Write-Host "   Вывод:" -ForegroundColor Gray
            $output | ForEach-Object { Write-Host "      $_" -ForegroundColor Gray }
            $failedTests++
            $results += [PSCustomObject]@{
                Service = $service
                Status = "FAILED"
                Color = "Red"
            }
        }
        
        Pop-Location
        $totalTests++
        Write-Host ""
    } else {
        Write-Host "⚠️  Тесты не найдены: $testFile" -ForegroundColor DarkYellow
        Write-Host ""
    }
}

Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "          ИТОГОВЫЙ ОТЧЕТ               " -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

foreach ($result in $results) {
    $icon = if ($result.Status -eq "PASSED") { "✅" } else { "❌" }
    Write-Host "$icon $($result.Service): $($result.Status)" -ForegroundColor $result.Color
}

Write-Host ""
Write-Host "Всего сервисов: $totalTests" -ForegroundColor White
Write-Host "Успешно: $passedTests" -ForegroundColor Green
Write-Host "Провалено: $failedTests" -ForegroundColor Red

$successRate = if ($totalTests -gt 0) { [math]::Round(($passedTests / $totalTests) * 100, 2) } else { 0 }
Write-Host "Процент успеха: $successRate%" -ForegroundColor $(if ($successRate -eq 100) { "Green" } elseif ($successRate -ge 80) { "Yellow" } else { "Red" })

Write-Host ""
if ($failedTests -eq 0) {
    Write-Host "🎉 Все тесты прошли успешно!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "⚠️  Некоторые тесты провалились. Проверьте вывод выше." -ForegroundColor Red
    exit 1
}
