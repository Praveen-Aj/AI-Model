# =========================================
# OLLAMA MANAGER V3 (ASCII STABILIZED)
# =========================================

# Change directory to the root project folder
Set-Location -Path "$PSScriptRoot"

# =========================
# UTILITIES
# =========================

function Write-Info {
    param([string]$Message)
    Write-Host "[*] $Message" -ForegroundColor Cyan
}

function Write-WarningMessage {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-ErrorMessage {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-SuccessMessage {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Resolve-OllamaPath {
    # Try command first (will work if PATH is updated)
    if (Get-Command ollama -ErrorAction SilentlyContinue) {
        return "ollama"
    }
    
    # Try known installation paths with specific user path first
    $knownPaths = @(
        "$env:USERPROFILE\AppData\Local\Programs\Ollama\ollama.exe",
        "C:\Users\Praveen\AppData\Local\Programs\Ollama\ollama.exe",
        "C:\Program Files\Ollama\ollama.exe"
    )
    
    foreach ($path in $knownPaths) {
        if (Test-Path $path) {
            return $path
        }
    }
    
    return $null
}

function Resolve-PythonPath {
    # Try command first (will work if PATH is updated)
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return "python"
    }
    
    # Try known installation paths
    $knownPaths = @(
        "$env:USERPROFILE\AppData\Local\Programs\Python\Python312\python.exe",
        "C:\Users\Praveen\AppData\Local\Programs\Python\Python312\python.exe",
        "C:\Program Files\Python312\python.exe"
    )
    
    foreach ($path in $knownPaths) {
        if (Test-Path $path) {
            return $path
        }
    }
    
    return $null
}

function Ensure-OllamaInstalled {
    $path = Resolve-OllamaPath
    if (-not $path) {
        Write-ErrorMessage "Ollama CLI not found. Please install Ollama."
        return $false
    }
    return $true
}

function Get-OllamaVersion {
    $path = Resolve-OllamaPath
    if (-not $path) {
        return $null
    }
    
    try {
        $versionOutput = & $path --version 2>&1
        if ($versionOutput -match "version is (\d+\.\d+\.\d+)") {
            return $matches[1]
        }
    }
    catch {
        return $null
    }
    
    return $null
}

function Check-OllamaVersionStability {
    $version = Get-OllamaVersion
    if (-not $version) {
        return
    }
    
    # Check for known problematic versions
    if ($version -eq "0.34.4") {
        Write-WarningMessage "Ollama version 0.34.4 has known stability issues."
        Write-Info "This version may experience crashes during model loading."
        Write-Info "Consider downgrading to Ollama 0.18.3 for better stability."
    }
}

function Get-OllamaStatus {
    if (-not (Ensure-OllamaInstalled)) {
        return "Not Installed"
    }

    try {
        $process = Get-Process ollama -ErrorAction SilentlyContinue
        if (-not $process) {
            return "Stopped"
        }

        # Try to connect to port using fast .NET socket client (200ms timeout)
        $socket = New-Object System.Net.Sockets.TcpClient
        $asyncResult = $socket.BeginConnect("127.0.0.1", 11434, $null, $null)
        $wait = $asyncResult.AsyncWaitHandle.WaitOne(200, $false)
        if ($wait -and $socket.Connected) {
            $socket.Close()
            return "Running"
        }
        $socket.Close()
        return "Starting/Unresponsive"
    }
    catch {
        return "Stopped"
    }
}

function Wait-ForOllama {
    param([int]$TimeoutSeconds = 20)

    $startTime = [DateTime]::UtcNow
    while (([DateTime]::UtcNow - $startTime).TotalSeconds -lt $TimeoutSeconds) {
        try {
            $socket = New-Object System.Net.Sockets.TcpClient
            $asyncResult = $socket.BeginConnect("127.0.0.1", 11434, $null, $null)
            $wait = $asyncResult.AsyncWaitHandle.WaitOne(500, $false)
            if ($wait -and $socket.Connected) {
                $socket.Close()
                return $true
            }
            $socket.Close()
        }
        catch {
            # ignore and retry
        }
        Start-Sleep -Seconds 1
    }
    return $false
}

function Get-LoadedModels {
    if (-not (Ensure-OllamaInstalled)) {
        return @()
    }

    try {
        # Use API to get proper JSON response instead of parsing CLI output
        $response = Invoke-RestMethod -Uri "http://localhost:11434/api/ps" -Method Get -TimeoutSec 10
        $models = @()
        if ($response.models) {
            foreach ($model in $response.models) {
                if ($model.name) {
                    $models += $model.name
                }
            }
        }
        return ,$models
    }
    catch {
        # Fallback to CLI parsing if API fails
        try {
            $path = Resolve-OllamaPath
            $lines = & $path ps 2>&1 | Where-Object { $_ -notmatch "ERROR|CHECK failed|generated\.c|mlx_compile_cache" } | Select-Object -Skip 1
            $models = @()
            foreach ($line in $lines) {
                $columns = $line -split '\s+', 2
                if ($columns.Count -ge 1 -and $columns[0].Trim()) {
                    $models += $columns[0].Trim()
                }
            }
            return ,$models
        }
        catch {
            return @()
        }
    }
}

function Get-InstalledModels {
    if (-not (Ensure-OllamaInstalled)) {
        return @()
    }

    try {
        $path = Resolve-OllamaPath
        $lines = & $path list 2>$null | Select-Object -Skip 1
        $models = @()
        foreach ($line in $lines) {
            if ($line.Trim()) {
                $models += $line.Trim()
            }
        }
        return ,$models
    }
    catch {
        return @()
    }
}

function Resolve-ModelPresets {
    $models = @(Get-InstalledModels)
    $coder = "qwen2.5-coder:14b"
    $chat = "qwen2.5-coder:14b"
    
    # Try to resolve dynamically from installed list
    $foundCoder = $null
    $foundChat = $null
    
    foreach ($m in $models) {
        $name = ($m -split '\s+')[0]
        if ($name -like "*coder*") {
            $foundCoder = $name
            break
        }
    }
    
    # For coding-focused workflow, default chat to coder if no separate chat model found
    foreach ($m in $models) {
        $name = ($m -split '\s+')[0]
        if (-not [string]::IsNullOrWhiteSpace($name) -and $name -notlike "*coder*" -and $name -notlike "*embed*") {
            $foundChat = $name
            break
        }
    }
    
    if ($foundCoder) {
        $coder = $foundCoder
    }
    if ($foundChat) {
        $chat = $foundChat
    } else {
        # Default to coder model for chat in coding-focused workflow
        $chat = $coder
    }
    
    return @{ Coder = $coder; Chat = $chat }
}

function Show-AvailableModels {
    $models = @(Get-InstalledModels)
    Write-Host ""
    Write-Host "-------------------------------" -ForegroundColor Cyan
    Write-Host "Available Ollama Models" -ForegroundColor Cyan
    Write-Host "-------------------------------" -ForegroundColor Cyan

    if (-not $models -or $models.Count -eq 0) {
        Write-WarningMessage "No available models found."
        return
    }

    $startIndex = 0
    if ($models[0] -match '(NAME|MODEL).*SIZE.*(CREATED|DATE)') {
        $startIndex = 1
    }

    $entries = @()
    for ($i = $startIndex; $i -lt $models.Count; $i++) {
        $line = $models[$i].Trim()
        if (-not $line) { continue }

        $parts = $line -split '\s{2,}'
        switch ($parts.Count) {
            4 { $entries += [pscustomobject]@{ Name = $parts[0]; Size = $parts[2]; Date = $parts[3] } }
            3 { $entries += [pscustomobject]@{ Name = $parts[0]; Size = $parts[1]; Date = $parts[2] } }
            2 { $entries += [pscustomobject]@{ Name = $parts[0]; Size = $parts[1]; Date = '' } }
            default { $entries += [pscustomobject]@{ Name = $parts[0]; Size = ''; Date = ($parts[1..($parts.Count-1)] -join ' ') } }
        }
    }

    if ($entries.Count -gt 0) {
        Write-Host ("{0,-45}{1,-15}{2}" -f "NAME", "SIZE", "DATE")
        Write-Host ("{0,-45}{1,-15}{2}" -f "----", "----", "----")
        foreach ($entry in $entries) {
            Write-Host ("{0,-45}{1,-15}{2}" -f $entry.Name, $entry.Size, $entry.Date)
        }
    }
    else {
        $index = 1
        foreach ($line in $models) {
            Write-Host "[$index] $line"
            $index++
        }
    }
}

function Show-LoadedModels {
    $models = @(Get-LoadedModels)
    Write-Host ""
    Write-Host "------------------------------" -ForegroundColor Cyan
    Write-Host "Currently Loaded Models" -ForegroundColor Cyan
    Write-Host "------------------------------" -ForegroundColor Cyan

    if (-not $models -or $models.Count -eq 0) {
        Write-WarningMessage "No models are currently loaded."
        return
    }

    $models | ForEach-Object { Write-Host "- $_" }
}

function Stop-SpecificModel {
    $loadedModels = @(Get-LoadedModels)
    if (-not $loadedModels -or $loadedModels.Count -eq 0) {
        Write-WarningMessage "No loaded models available to stop."
        return
    }

    Write-Host ""
    Write-Host "Choose a model to stop:" -ForegroundColor Cyan
    for ($i = 0; $i -lt $loadedModels.Count; $i++) {
        Write-Host "[$($i + 1)] $($loadedModels[$i])"
    }

    $selection = Read-Host "Enter model number or exact name"
    if (-not $selection) {
        Write-WarningMessage "No selection entered."
        return
    }

    if ($selection -as [int] -and $selection -ge 1 -and $selection -le $loadedModels.Count) {
        $modelName = $loadedModels[$selection - 1]
    }
    else {
        $modelName = $loadedModels | Where-Object { $_ -ieq $selection }
    }

    if (-not $modelName) {
        Write-ErrorMessage "Invalid model selection."
        return
    }

    Stop-Model $modelName
}

function Pause-Script {
    Read-Host "Press Enter to continue..."
}

# =========================
# COMMANDS
# =========================

function Get-NvidiaSmiPath {
    # Try using where command first (most reliable)
    try {
        $whereResult = where.exe nvidia-smi 2>$null
        if ($whereResult) {
            return $whereResult.Trim()
        }
    }
    catch {
        # Ignore errors and continue
    }
    
    # Try command via Get-Command
    if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
        return "nvidia-smi"
    }
    
    # Try common installation paths
    $paths = @(
        "C:\Windows\System32\nvidia-smi.exe",
        "C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe",
        "C:\Program Files\NVIDIA Corporation\NVIDIA App\nvidia-smi.exe"
    )
    foreach ($path in $paths) {
        if (Test-Path $path) {
            return $path
        }
    }
    
    return $null
}

function Start-Ollama {
    $path = Resolve-OllamaPath
    if (-not $path) {
        Write-ErrorMessage "Ollama CLI not found."
        return
    }

    $status = Get-OllamaStatus
    if ($status -eq "Running") {
        Write-SuccessMessage "Ollama is already running and responding."
        return
    }

    # Clean up zombie process if present but unresponsive
    $process = Get-Process ollama -ErrorAction SilentlyContinue
    if ($process) {
        Write-WarningMessage "Ollama process is present but unresponsive. Restarting it..."
        Stop-Process -Name ollama -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }

    Write-Info "Starting Ollama service..."
    Start-Process $path -ArgumentList "serve" -WindowStyle Hidden

    if (Wait-ForOllama -TimeoutSeconds 20) {
        Write-SuccessMessage "Ollama started successfully."
    }
    else {
        Write-ErrorMessage "Ollama process started, but failed to respond on port 11434."
        Write-WarningMessage "This may indicate Ollama version 0.34.4 stability issues."
        Write-Info "Consider downgrading to Ollama 0.18.3 for better stability."
    }
}

function Load-Model {
    param([string]$Model)

    Write-Host ""
    Write-Info "Loading model: $Model..."

    $loadedModels = @(Get-LoadedModels)
    if ($loadedModels -contains $Model) {
        Write-WarningMessage "Model '$Model' is already loaded."
        return
    }

    # Select correct API endpoint based on model type (embed vs text)
    $endpoint = "api/generate"
    $body = @{ model = $Model }
    
    if ($Model -like "*embed*") {
        $endpoint = "api/embeddings"
        $body = @{
            model = $Model
            prompt = "warmup"
        }
    }
    
    $payload = $body | ConvertTo-Json

    try {
        Invoke-RestMethod -Uri "http://localhost:11434/$endpoint" -Method Post -Body $payload -ContentType "application/json" -TimeoutSec 180 | Out-Null
        
        # Verify the model was actually loaded with multiple attempts
        $loaded = $false
        for ($i = 0; $i -lt 3; $i++) {
            Start-Sleep -Seconds 2
            $newLoadedModels = @(Get-LoadedModels)
            if ($newLoadedModels -contains $Model) {
                $loaded = $true
                break
            }
        }
        
        if ($loaded) {
            Write-SuccessMessage "Loaded: $Model"
        }
        else {
            Write-WarningMessage "Model '$Model' may not have loaded correctly (API verification failed)."
            Write-Info "The model load request was sent, but API verification did not confirm it."
        }
    }
    catch {
        Write-ErrorMessage "Error loading model ${Model} - $_"
        
        # Check if Ollama crashed during model load
        $ollamaStatus = Get-OllamaStatus
        if ($ollamaStatus -ne "Running") {
            Write-Host ""
            Write-ErrorMessage "Ollama server has crashed during model load!"
            Write-WarningMessage "This is likely due to Ollama 0.34.4 stability issues."
            Write-Info "Recommendation: Use Option 10 to kill Ollama, then Option 5 to restart it."
            Write-Info "Or consider downgrading to Ollama 0.18.3 for better stability."
        }
    }
}

function Stop-Model {
    param([string]$Model)

    $loadedModels = @(Get-LoadedModels)
    if (-not ($loadedModels -contains $Model)) {
        Write-WarningMessage "Model '$Model' is not loaded."
        return
    }

    Write-Host ""
    Write-WarningMessage "Stopping model: $Model"

    # API request payload to unload model instantly
    $payload = @{
        model = $Model
        keep_alive = 0
    } | ConvertTo-Json

    try {
        Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post -Body $payload -ContentType "application/json" -TimeoutSec 10 | Out-Null
        Start-Sleep -Seconds 2
        
        # Verify the model was actually stopped
        $stillLoaded = @(Get-LoadedModels)
        if ($stillLoaded -contains $Model) {
            Write-WarningMessage "Model '$Model' may still be loaded."
        }
        else {
            Write-SuccessMessage "Stopped: $Model"
        }
    }
    catch {
        Write-ErrorMessage "Error stopping model ${Model} - $_"
    }
}

function Show-Status {
    $status = Get-OllamaStatus
    Write-Host ""
    Write-Host "=============================" -ForegroundColor Cyan
    Write-Host "Ollama Service Status: $status"
    Write-Host "=============================" -ForegroundColor Cyan

    if ($status -eq "Running") {
        $path = Resolve-OllamaPath
        try {
            $rawOutput = & $path ps 2>&1
            $output = $rawOutput | Where-Object { 
                $_ -notmatch "ERROR" -and 
                $_ -notmatch "CHECK failed" -and 
                $_ -notmatch "generated\.c" -and
                $_ -notmatch "mlx_compile_cache"
            }
            
            if ($output -and $output.Count -gt 0) {
                $output | ForEach-Object { Write-Host $_ }
            }
            else {
                Write-Host "No models currently loaded in memory (Ollama command had issues)."
            }
        }
        catch {
            Write-WarningMessage "Could not retrieve model status: $_"
        }
        
        # Try to get loaded models via API as fallback
        Write-Host ""
        Write-Host "Loaded Models (via API):" -ForegroundColor Cyan
        $loadedModels = @(Get-LoadedModels)
        if ($loadedModels.Count -gt 0) {
            $loadedModels | ForEach-Object { Write-Host "- $_" }
        }
        else {
            Write-Host "No models loaded."
        }
    }

    Write-Host ""
    Write-Host "GPU Memory Usage:" -ForegroundColor Cyan
    try {
        $smiPath = Get-NvidiaSmiPath
        if ($smiPath) {
            Write-Info "Using nvidia-smi at: $smiPath"
            $gpuLines = & $smiPath --query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>$null
            if ($LASTEXITCODE -eq 0 -and $gpuLines) {
                Write-Host "Name, Temp(C), GPU%, Memory Used/Total"
                $gpuLines | ForEach-Object {
                    $parts = $_ -split ',\s*'
                    if ($parts.Count -ge 5) {
                        $outputLine = "{0}, {1}C, {2}%, {3}MiB / {4}MiB" -f $parts[0], $parts[1], $parts[2], $parts[3], $parts[4]
                        Write-Host $outputLine
                    }
                    else {
                        Write-Host $_
                    }
                }
            }
            else {
                Write-WarningMessage "nvidia-smi query failed, showing full output:"
                & $smiPath
            }
        }
        else {
            Write-WarningMessage "nvidia-smi not available."
        }
    }
    catch {
        Write-WarningMessage "nvidia-smi error: $_"
    }
    Write-Host ""
}

function Stop-AllModels {
    $loadedModels = @(Get-LoadedModels)
    if (-not $loadedModels -or $loadedModels.Count -eq 0) {
        Write-WarningMessage "No models loaded."
        return
    }

    Write-Host ""
    Write-Info "Stopping all loaded models..."
    $stoppedCount = 0
    
    foreach ($model in $loadedModels) {
        Stop-Model $model
        $stoppedCount++
    }
    
    # Verify all models are actually stopped
    Start-Sleep -Seconds 2
    $remainingModels = @(Get-LoadedModels)
    
    Write-Host ""
    if ($remainingModels.Count -eq 0) {
        Write-SuccessMessage "All loaded models stopped successfully ($stoppedCount models)."
    }
    else {
        Write-WarningMessage "Some models may still be loaded:"
        $remainingModels | ForEach-Object { Write-Host "- $_" }
    }
    
    # Show verification
    Show-ModelVerification
}

function Show-ModelVerification {
    Write-Host ""
    Write-Host "=============================" -ForegroundColor Cyan
    Write-Host "Model State Verification" -ForegroundColor Cyan
    Write-Host "=============================" -ForegroundColor Cyan
    
    $loadedModels = @(Get-LoadedModels)
    Write-Host "Loaded models: $($loadedModels.Count)"
    if ($loadedModels.Count -gt 0) {
        $loadedModels | ForEach-Object { Write-Host "- $_" }
    }
    else {
        Write-Host "No models loaded."
    }
    
    # Show GPU memory using the same method as Show-Status
    Write-Host ""
    Write-Host "GPU Memory Usage:" -ForegroundColor Cyan
    try {
        $smiPath = Get-NvidiaSmiPath
        if ($smiPath) {
            $gpuLines = & $smiPath --query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>$null
            if ($LASTEXITCODE -eq 0 -and $gpuLines) {
                Write-Host "Name, Temp(C), GPU%, Memory Used/Total"
                $gpuLines | ForEach-Object {
                    $parts = $_ -split ',\s*'
                    if ($parts.Count -ge 5) {
                        $outputLine = "{0}, {1}C, {2}%, {3}MiB / {4}MiB" -f $parts[0], $parts[1], $parts[2], $parts[3], $parts[4]
                        Write-Host $outputLine
                    }
                    else {
                        Write-Host $_
                    }
                }
            }
            else {
                Write-WarningMessage "nvidia-smi query failed."
            }
        }
        else {
            Write-WarningMessage "nvidia-smi not available."
        }
    }
    catch {
        Write-WarningMessage "GPU memory query error: $_"
    }
    Write-Host ""
}

function Kill-Ollama {
    Write-Host ""
    Write-ErrorMessage "Terminating Ollama service..."

    $process = Get-Process ollama -ErrorAction SilentlyContinue
    if ($process) {
        Stop-Process -Name ollama -Force -ErrorAction SilentlyContinue
        Write-SuccessMessage "Ollama terminated."
    }
    else {
        Write-WarningMessage "Ollama is not running."
    }
}

# =========================
# MENU LOOP
# =========================

$EmbedModel = "nomic-embed-text:latest"

while ($true) {
    Clear-Host

    # Check Ollama version stability on first run
    if (-not $script:OllamaVersionChecked) {
        Check-OllamaVersionStability
        $script:OllamaVersionChecked = $true
    }

    $serviceStatus = Get-OllamaStatus
    $presets = Resolve-ModelPresets
    $CoderModel = $presets.Coder

    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "         OLLAMA MODEL MANAGER V3" -ForegroundColor Magenta
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "Service status: $serviceStatus" -ForegroundColor Green
    Write-Host ""

    Write-Host "1. Launch Desktop GUI Manager" -ForegroundColor Yellow
    Write-Host ""

    Write-Host "2. Start Coding Mode" -ForegroundColor Yellow
    Write-Host "   - Qwen2.5-Coder 14B" -ForegroundColor Cyan
    Write-Host "   - Optimized for Claude Code / Continue" -ForegroundColor Cyan
    Write-Host "   - No embedding model" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "3. Start Full AI Mode" -ForegroundColor Yellow
    Write-Host "   - Qwen2.5-Coder 14B" -ForegroundColor Cyan
    Write-Host "   - Nomic Embed" -ForegroundColor Cyan
    Write-Host "   - Loads all configured AI models" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "4. Launch Claude Code" -ForegroundColor Yellow
    Write-Host "   - Qwen2.5-Coder 14B" -ForegroundColor Cyan
    Write-Host "   - Runs: ollama launch claude --model qwen2.5-coder:14b" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "5. Start Ollama Only" -ForegroundColor Yellow
    Write-Host "   - Start Ollama service without loading models"
    Write-Host ""

    Write-Host "6. Show Status & Loaded Models" -ForegroundColor Yellow
    Write-Host ""

    Write-Host "7. Show Available Models" -ForegroundColor Yellow
    Write-Host ""

    Write-Host "8. Stop Specific Model" -ForegroundColor Yellow
    Write-Host ""

    Write-Host "9. Stop All Models" -ForegroundColor Yellow
    Write-Host ""

    Write-Host "10. Kill Ollama Service Completely" -ForegroundColor Yellow
    Write-Host ""

    Write-Host "0. Exit" -ForegroundColor Yellow
    Write-Host ""

    $choice = Read-Host "Select option"

    switch ($choice) {
        "1" {
            Write-Info "Booting Ollama backend..."
            Start-Ollama
            Write-Info "Starting PySide6 GUI app..."
            $pythonPath = Resolve-PythonPath
            if ($pythonPath) {
                & $pythonPath main.py
            } else {
                Write-ErrorMessage "Python not found. Please install Python or add it to PATH."
            }
            Pause-Script
        }

        "2" {
            Start-Ollama
            Write-Info "Loading Qwen for coding (optimized for Claude Code)..."
            
            # Check current loaded models and unload embedding model if present
            $loadedModels = @(Get-LoadedModels)
            if ($loadedModels -contains $EmbedModel) {
                Write-Info "Stopping embedding model to free GPU memory..."
                Stop-Model $EmbedModel
            }
            
            # Load Qwen only if not already loaded
            if (-not ($loadedModels -contains $CoderModel)) {
                Load-Model $CoderModel
            }
            else {
                Write-SuccessMessage "$CoderModel is already loaded."
            }
            
            # Verify final state
            Write-Host ""
            Write-Info "Verifying coding mode state..."
            Show-ModelVerification
            
            Show-Status
            Pause-Script
        }

        "3" {
            Start-Ollama
            Write-Info "Loading Full AI Mode..."
            # For full AI mode, load both coder and embedding models
            Load-Model $CoderModel
            Load-Model $EmbedModel
            
            # Verify final state
            Write-Host ""
            Write-Info "Verifying Full AI Mode state..."
            Show-ModelVerification
            
            Show-Status
            Pause-Script
        }

        "4" {
            Write-Info "Preparing for Claude Code..."
            Start-Ollama
            
            # Check if Qwen is already loaded
            $loadedModels = @(Get-LoadedModels)
            if ($loadedModels -contains $CoderModel) {
                Write-SuccessMessage "$CoderModel is already loaded."
            }
            else {
                Write-Info "Loading $CoderModel..."
                Load-Model $CoderModel
            }
            
            # Set environment variable for unknown model handling
            $env:CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT = "1"
            Write-Info "Set CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT=1 for Qwen compatibility"
            
            Write-Info "Launching Claude Code with Qwen model..."
            $ollamaPath = Resolve-OllamaPath
            if ($ollamaPath) {
                try {
                    Write-Host ""
                    Write-Host "========================================" -ForegroundColor Cyan
                    Write-Host "Claude Code launching with:" -ForegroundColor Green
                    Write-Host "Model: $CoderModel" -ForegroundColor Cyan
                    Write-Host "Context: 32,768 tokens (Qwen actual)" -ForegroundColor Cyan
                    Write-Host "========================================" -ForegroundColor Cyan
                    Write-Host ""
                    
                    & $ollamaPath launch claude --model $CoderModel
                }
                catch {
                    Write-ErrorMessage "Failed to launch Claude Code: $_"
                    Write-Info "You may need to install Claude Code separately."
                }
            }
            else {
                Write-ErrorMessage "Ollama not found."
            }
            Pause-Script
        }

        "5" {
            Start-Ollama
            Pause-Script
        }

        "6" {
            Show-Status
            Pause-Script
        }

        "7" {
            Show-AvailableModels
            Pause-Script
        }

        "8" {
            Stop-SpecificModel
            Pause-Script
        }

        "9" {
            Stop-AllModels
            Pause-Script
        }

        "10" {
            Stop-AllModels
            Kill-Ollama
            Pause-Script
        }

        "0" {
            exit 0
        }

        default {
            Write-Host ""
            Write-ErrorMessage "Invalid option."
            Pause-Script
        }
    }
}