# Cash Forecast Analyzer - Startup Script
# Run this to start the Flask application

Write-Host "🚀 Starting Cash Forecast Analyzer..." -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Run: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "📦 Activating virtual environment..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found! Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✏️  Please edit .env and add your OPENAI_API_KEY" -ForegroundColor Yellow
}

# Check if OpenAI API key is set
$envContent = Get-Content ".env" -Raw
if ($envContent -match "OPENAI_API_KEY=\s*$" -or $envContent -notmatch "OPENAI_API_KEY=") {
    Write-Host ""
    Write-Host "⚠️  WARNING: OPENAI_API_KEY not set in .env file" -ForegroundColor Yellow
    Write-Host "The app will run, but OpenAI features won't work without an API key" -ForegroundColor Yellow
    Write-Host ""
}

# Start Flask app
Write-Host ""
Write-Host "🌐 Starting Flask server on http://localhost:5000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

python app.py
