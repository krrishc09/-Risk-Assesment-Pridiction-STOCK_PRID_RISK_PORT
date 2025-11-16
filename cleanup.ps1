# cleanup.ps1
# Script to remove duplicate and old files

Write-Host "Portfolio Platform Cleanup Script" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$filesToDelete = @(
    # Old documentation
    "README.md",
    "README_PLATFORM.md",
    "DEPLOYMENT_GUIDE.md",
    "RISK_MODELS_GUIDE.md",
    "PREDICTION_GUIDE.md",
    "COMPLETE_FEATURES.md",
    "QUICKSTART.md",
    "frontend_setup.md",
    
    # Old test files
    "test_platform.py",
    "test_risk_models.py",
    "test_predictions.py",
    "test_api.py",
    
    # Old config files
    "config.py",
    "requirements_minimal.txt",
    "requirements_platform.txt",
    
    # Old main file
    "main.py"
)

Write-Host "Files to be deleted:" -ForegroundColor Yellow
foreach ($file in $filesToDelete) {
    if (Test-Path $file) {
        Write-Host "  [X] $file" -ForegroundColor Red
    }
}

Write-Host ""
$response = Read-Host "Do you want to delete these files? (yes/no)"

if ($response -eq "yes") {
    $deletedCount = 0
    foreach ($file in $filesToDelete) {
        if (Test-Path $file) {
            Remove-Item $file -Force
            Write-Host "[OK] Deleted: $file" -ForegroundColor Green
            $deletedCount++
        }
    }
    
    Write-Host ""
    Write-Host "[OK] Cleanup complete! Deleted $deletedCount files" -ForegroundColor Green
    Write-Host ""
    Write-Host "Essential files remaining:" -ForegroundColor Cyan
    Write-Host "   - main_platform.py" -ForegroundColor White
    Write-Host "   - database.py" -ForegroundColor White
    Write-Host "   - requirements.txt" -ForegroundColor White
    Write-Host "   - README_COMPLETE.md" -ForegroundColor White
    Write-Host "   - test_all.py" -ForegroundColor White
    Write-Host "   - START_HERE.md" -ForegroundColor White
    Write-Host ""
    Write-Host "You can now start with: python main_platform.py" -ForegroundColor Green
} else {
    Write-Host "[X] Cleanup cancelled" -ForegroundColor Yellow
}
