# Startup script for Local AI Model Manager
# Ensures Ollama is running and starts the Streamlit application

Write-Host "🤖 Starting Local AI Model Manager..." -ForegroundColor Green

# Check if Ollama is running
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434" -TimeoutSec 5
    Write-Host "✅ Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Ollama is not running. Starting it..." -ForegroundColor Yellow
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    
    # Wait for Ollama to start
    $maxAttempts = 30
    $attempt = 0
    
    while ($attempt -lt $maxAttempts) {
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:11434" -TimeoutSec 2
            Write-Host "✅ Ollama started successfully" -ForegroundColor Green
            break
        } catch {
            $attempt++
            Write-Host "⏳ Waiting for Ollama to start... ($attempt/$maxAttempts)" -ForegroundColor Yellow
            Start-Sleep -Seconds 2
        }
    }
    
    if ($attempt -eq $maxAttempts) {
        Write-Host "❌ Failed to start Ollama. Please start it manually with: ollama serve" -ForegroundColor Red
        exit 1
    }
}

# Check if required Python packages are installed
Write-Host "🔍 Checking dependencies..." -ForegroundColor Blue

# Check if packages are available using pip list
$packages = @("streamlit", "aiohttp", "psutil", "plotly", "pandas")

foreach ($package in $packages) {
    try {
        $result = pip show $package 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $package is available" -ForegroundColor Green
        } else {
            Write-Host "❌ $package not found. Installing..." -ForegroundColor Yellow
            pip install $package
        }
    } catch {
        Write-Host "❌ Error checking $package" -ForegroundColor Red
    }
}

# Create data directory if it doesn't exist
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
    Write-Host "📁 Created data directory" -ForegroundColor Green
}

# Start the Model Manager
Write-Host "🚀 Starting Model Manager web interface..." -ForegroundColor Green
Write-Host "📍 Opening browser at http://localhost:8501" -ForegroundColor Blue

# Start Streamlit in the background
Start-Process "streamlit" -ArgumentList "run app.py", "--server.port 8501", "--server.headless true"

# Wait a moment for the server to start
Start-Sleep -Seconds 3

# Open browser
Start-Process "http://localhost:8501"

Write-Host "✅ Model Manager is running!" -ForegroundColor Green
Write-Host "💡 Press Ctrl+C to stop the server" -ForegroundColor Gray

# Keep the script running
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} catch {
    Write-Host "`n🛑 Stopping Model Manager..." -ForegroundColor Yellow
    Write-Host "👋 Goodbye!" -ForegroundColor Green
}
