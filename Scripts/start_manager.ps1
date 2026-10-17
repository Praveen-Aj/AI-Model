# Startup script for Local AI Model Manager

Write-Host "Starting Local AI Model Manager..." -ForegroundColor Green

# Check if Ollama is running
try {
    Invoke-RestMethod -Uri "http://localhost:11434" -TimeoutSec 5 | Out-Null
    Write-Host "Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "Starting Ollama..." -ForegroundColor Yellow
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    
    $maxAttempts = 30
    $attempt = 0
    
    while ($attempt -lt $maxAttempts) {
        try {
            Invoke-RestMethod -Uri "http://localhost:11434" -TimeoutSec 2 | Out-Null
            Write-Host "Ollama started successfully" -ForegroundColor Green
            break
        } catch {
            $attempt++
            Write-Host "Waiting for Ollama to start... ($attempt/$maxAttempts)" -ForegroundColor Yellow
            Start-Sleep -Seconds 2
        }
    }
    
    if ($attempt -eq $maxAttempts) {
        Write-Host "Failed to start Ollama. Please start it manually with: ollama serve" -ForegroundColor Red
        exit 1
    }
}

# Install dependencies
Write-Host "Checking dependencies..." -ForegroundColor Blue

$packages = @("streamlit", "aiohttp", "psutil", "plotly", "pandas")

foreach ($package in $packages) {
    pip show $package 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing $package..." -ForegroundColor Yellow
        pip install $package
    }
}

# Create data directory
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
    Write-Host "Created data directory" -ForegroundColor Green
}

# Start application
Write-Host "Starting Model Manager web interface..." -ForegroundColor Green
Write-Host "Opening browser at http://localhost:8501" -ForegroundColor Blue

Start-Process "streamlit" -ArgumentList "run app.py","--server.port 8501","--server.headless true"
Start-Sleep -Seconds 3
Start-Process "http://localhost:8501"

Write-Host "Model Manager is running!" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray

try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} catch {
    Write-Host "Stopping Model Manager..." -ForegroundColor Yellow
    Write-Host "Goodbye!" -ForegroundColor Green
}
