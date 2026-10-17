# Startup script for Local AI Model Manager Desktop Application
# Checks dependencies and launches the PySide6 desktop app

# Change to project root directory
Set-Location -Path "$PSScriptRoot\.."

Write-Host "[*] Starting Local AI Model Manager Desktop Application..." -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version 2>$null
    Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}

# Check if required packages are installed
Write-Host "[*] Checking dependencies..." -ForegroundColor Blue

$packages = @("PySide6", "psutil", "aiohttp")

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

# Create data directory if it doesn't exist
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
    Write-Host "[OK] Created data directory" -ForegroundColor Green
}

# Create logs directory if it doesn't exist
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
    Write-Host "[OK] Created logs directory" -ForegroundColor Green
}

# Start the Desktop Application
Write-Host "[*] Starting Local AI Model Manager Desktop Application..." -ForegroundColor Green

try {
    python main.py
} catch {
    Write-Host "[ERROR] Failed to start desktop application: $_" -ForegroundColor Red
    Write-Host "[HELP] Try running: python main.py" -ForegroundColor Yellow
    exit 1
}

Write-Host "Goodbye!" -ForegroundColor Green
