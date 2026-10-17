# =========================
# OLLAMA MANAGER
# =========================

$ChatModel  = "qwen2.5:14b"
$CoderModel = "qwen2.5-coder:7b"
$EmbedModel = "nomic-embed-text:latest"

# =========================
# FUNCTIONS
# =========================

function Start-Ollama {

    $existing = Get-Process ollama -ErrorAction SilentlyContinue

    if (-not $existing) {
        Write-Host ""
        Write-Host "Starting Ollama service..." -ForegroundColor Cyan

        Start-Process "ollama"

        Start-Sleep -Seconds 5

        Write-Host "Ollama started." -ForegroundColor Green
    }
    else {
        Write-Host ""
        Write-Host "Ollama already running." -ForegroundColor Yellow
    }
}

function Load-Model {
    param([string]$Model)

    Write-Host ""
    Write-Host "Loading model: $Model" -ForegroundColor Cyan

    ollama run $Model "hello" | Out-Null

    Write-Host "Loaded: $Model" -ForegroundColor Green
}

function Stop-Model {
    param([string]$Model)

    $loaded = ollama ps | Select-String $Model

    if ($loaded) {

        Write-Host ""
        Write-Host "Stopping model: $Model" -ForegroundColor Yellow

        ollama stop $Model | Out-Null

        Start-Sleep -Seconds 2

        Write-Host "Stopped: $Model" -ForegroundColor Green
    }
}

function Show-Status {

    Write-Host ""
    Write-Host "=============================" -ForegroundColor Cyan
    Write-Host "Loaded Ollama Models"
    Write-Host "=============================" -ForegroundColor Cyan

    ollama ps

    Write-Host "GPU Memory Usage:" -ForegroundColor Cyan
    nvidia-smi

    Write-Host ""
}

function Stop-AllModels {

    Stop-Model $ChatModel
    Stop-Model $CoderModel
    Stop-Model $EmbedModel

    Write-Host ""
    Write-Host "All models stopped." -ForegroundColor Green
}

function Kill-Ollama {

    Write-Host ""
    Write-Host "Terminating Ollama..." -ForegroundColor Red

    taskkill /F /IM ollama.exe | Out-Null

    Write-Host "Ollama terminated." -ForegroundColor Green
}

# =========================
# MENU
# =========================

while ($true) {

    Clear-Host

    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "         OLLAMA MODEL MANAGER"
    Write-Host "=========================================" -ForegroundColor Cyan

    Write-Host ""
    Write-Host "1. Start Coding Mode"
    Write-Host "   - Loads coder + embeddings"
    Write-Host ""

    Write-Host "2. Start Full AI Mode"
    Write-Host "   - Loads chat + coder + embeddings"
    Write-Host ""

    Write-Host "3. Show Loaded Models"
    Write-Host ""

    Write-Host "4. Stop All Models"
    Write-Host ""

    Write-Host "5. Kill Ollama Completely"
    Write-Host ""

    Write-Host "6. Exit"
    Write-Host ""

    $choice = Read-Host "Select option"

    switch ($choice) {

        "1" {

            Start-Ollama

            Load-Model $CoderModel
            Load-Model $EmbedModel

            Show-Status

            Pause
        }

        "2" {

            Start-Ollama

            Load-Model $ChatModel
            Load-Model $CoderModel
            Load-Model $EmbedModel

            Show-Status

            Pause
        }

        "3" {

            Show-Status

            Pause
        }

        "4" {

            Stop-AllModels

            Show-Status

            Pause
        }

        "5" {

            Stop-AllModels

            Kill-Ollama

            Pause
        }

        "6" {

            break
        }

        default {

            Write-Host ""
            Write-Host "Invalid option." -ForegroundColor Red

            Pause
        }
    }
}