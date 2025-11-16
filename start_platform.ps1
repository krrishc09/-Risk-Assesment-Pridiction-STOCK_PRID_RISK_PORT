# start_platform.ps1
# Quick start script for Real-Time Portfolio Analysis Platform

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Real-Time Portfolio Analysis Platform" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "   Run: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "📦 Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Check if requirements are installed
Write-Host "🔍 Checking dependencies..." -ForegroundColor Yellow
$packages = pip list
if ($packages -notmatch "fastapi") {
    Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
    pip install -q -r requirements_platform.txt
    Write-Host "✅ Dependencies installed!" -ForegroundColor Green
} else {
    Write-Host "✅ Dependencies already installed" -ForegroundColor Green
}

# Initialize database
Write-Host "🗄️  Initializing database..." -ForegroundColor Yellow
python -c "from database import init_database; init_database(); print('✅ Database initialized!')"

Write-Host ""
Write-Host "🚀 Starting platform..." -ForegroundColor Green
Write-Host ""
Write-Host "📍 Platform URLs:" -ForegroundColor Cyan
Write-Host "   API: http://localhost:8000" -ForegroundColor White
Write-Host "   Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   Health: http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "💡 To test the platform:" -ForegroundColor Yellow
Write-Host "   Open a new terminal and run: python test_platform.py" -ForegroundColor White
Write-Host ""
Write-Host "⏹️  Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the platform
python main_platform.py
