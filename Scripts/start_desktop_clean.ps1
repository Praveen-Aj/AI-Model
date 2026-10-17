# Clean startup script for Local AI Model Manager Desktop Application
# No Unicode characters to avoid encoding issues

Write-Host "Starting Local AI Model Manager Desktop Application..." -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version 2>$null
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}

# Check if required packages are installed
Write-Host "Checking dependencies..." -ForegroundColor Blue

$packages = @("PySide6", "psutil", "aiohttp")

foreach ($package in $packages) {
    try {
        pip show $package 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "$package is available" -ForegroundColor Green
        } else {
            Write-Host "$package not found. Installing..." -ForegroundColor Yellow
            pip install $package
        }
    } catch {
        Write-Host "Error checking $package" -ForegroundColor Red
    }
}

# Check if Ollama is running
try {
    Invoke-RestMethod -Uri "http://localhost:11434" -TimeoutSec 5 | Out-Null
    Write-Host "Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "Ollama is not running. Starting it..." -ForegroundColor Yellow
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    
    # Wait for Ollama to start
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

# Create data directory if it doesn't exist
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
    Write-Host "Created data directory" -ForegroundColor Green
}

# Create logs directory if it doesn't exist
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
    Write-Host "Created logs directory" -ForegroundColor Green
}

# Start the Desktop Application
Write-Host "Starting Local AI Model Manager Desktop Application..." -ForegroundColor Green

try {
    python main.py
} catch {
    Write-Host "Failed to start desktop application: $_" -ForegroundColor Red
    Write-Host "Try running: python main.py" -ForegroundColor Yellow
    exit 1
}

Write-Host "Goodbye!" -ForegroundColor Green
