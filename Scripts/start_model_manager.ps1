# Startup script for Local AI Model Manager
# Ensures Ollama is running and starts Streamlit application

# Change to project root directory
Set-Location -Path "$PSScriptRoot\.."

Write-Host "[*] Starting Local AI Model Manager..." -ForegroundColor Green

# Check if Ollama is running
try {
    Invoke-RestMethod -Uri "http://localhost:11434" -TimeoutSec 5 | Out-Null
    Write-Host "[OK] Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Ollama is not running. Starting it..." -ForegroundColor Yellow
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    
    # Wait for Ollama to start
    $maxAttempts = 30
    $attempt = 0
    
    while ($attempt -lt $maxAttempts) {
        try {
            Invoke-RestMethod -Uri "http://localhost:11434" -TimeoutSec 2 | Out-Null
            Write-Host "[OK] Ollama started successfully" -ForegroundColor Green
            break
        } catch {
            $attempt++
            Write-Host "[WAIT] Waiting for Ollama to start... ($attempt/$maxAttempts)" -ForegroundColor Yellow
            Start-Sleep -Seconds 2
        }
    }
    
    if ($attempt -eq $maxAttempts) {
        Write-Host "[ERROR] Failed to start Ollama. Please start it manually with: ollama serve" -ForegroundColor Red
        exit 1
    }
}

# Check if required Python packages are installed
Write-Host "[*] Checking dependencies..." -ForegroundColor Blue

# Check if packages are available using pip list
$packages = @("streamlit", "aiohttp", "psutil", "plotly", "pandas")

foreach ($package in $packages) {
    try {
        pip show $package 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] $package is available" -ForegroundColor Green
        } else {
            Write-Host "[WARN] $package not found. Installing..." -ForegroundColor Yellow
            pip install $package
        }
    } catch {
        Write-Host "[ERROR] Error checking $package" -ForegroundColor Red
    }
}

# Create data directory if it doesn't exist
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
    Write-Host "[OK] Created data directory" -ForegroundColor Green
}

# Start Model Manager
Write-Host "[*] Starting Model Manager web interface..." -ForegroundColor Green
Write-Host "[*] Opening browser at http://localhost:8501" -ForegroundColor Blue

# Start Streamlit in background
Start-Process "streamlit" -ArgumentList "run app.py","--server.port 8501","--server.headless true"

# Wait a moment for the server to start
Start-Sleep -Seconds 3

# Open browser
Start-Process "http://localhost:8501"

Write-Host "[OK] Model Manager is running!" -ForegroundColor Green
Write-Host "[HELP] Press Ctrl+C to stop the server" -ForegroundColor Gray

# Keep the script running
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} catch {
    Write-Host "`n[!] Stopping Model Manager..." -ForegroundColor Yellow
    Write-Host "Goodbye!" -ForegroundColor Green
}
