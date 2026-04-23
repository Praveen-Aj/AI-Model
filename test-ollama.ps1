# Test Ollama and models

Write-Host "Testing Ollama Setup..." -ForegroundColor Cyan
Write-Host ""

# Test Ollama service
Write-Host "1️⃣  Testing Ollama service..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434" -ErrorAction Stop
    Write-Host "   ✅ Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Ollama service not responding. Start it with: ollama serve" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "2️⃣  Testing Qwen2.5-Coder model..." -ForegroundColor Yellow

# Test model
$json = @{
    model = "qwen2.5-coder:14b"
    prompt = "def hello():"
    stream = $false
} | ConvertTo-Json

try {
    $result = Invoke-WebRequest -Uri "http://localhost:11434/api/generate" `
        -Method Post `
        -ContentType "application/json" `
        -Body $json -ErrorAction Stop
    
    Write-Host "   ✅ Model responds correctly" -ForegroundColor Green
    $response = $result.Content | ConvertFrom-Json
    Write-Host "   Response sample: $($response.response.Substring(0, 50))..." -ForegroundColor Green
} catch {
    Write-Host "   ❌ Model not responding" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "3️⃣  Testing Aider..." -ForegroundColor Yellow
try {
    aider --version
    Write-Host "   ✅ Aider is installed" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Aider not found. Install with: pip install aider-chat" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "4️⃣  Testing Continue integration..." -ForegroundColor Yellow
Write-Host "   📝 Continue extension must be installed in VS Code" -ForegroundColor Yellow
Write-Host "   Config should point to: http://localhost:11434" -ForegroundColor Yellow

Write-Host ""
Write-Host "✅ All systems ready!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Install 'Continue' extension in VS Code"
Write-Host "2. Configure Continue settings (see SETUP_LOCAL_AI.md)"
Write-Host "3. Run: aider-start.ps1 for interactive mode"
Write-Host "4. Or run: aider-auto.ps1 for autonomous mode"
