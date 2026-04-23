# Test Ollama and models

Write-Host "Testing Ollama Setup..." -ForegroundColor Cyan
Write-Host ""

# Test Ollama service
Write-Host "1. Testing Ollama service..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434" -ErrorAction Stop
    Write-Host "   OK - Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "   FAIL - Ollama service not responding. Start it with: ollama serve" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "2. Testing Qwen2.5-Coder model..." -ForegroundColor Yellow

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
    
    Write-Host "   OK - Model responds correctly" -ForegroundColor Green
    $response = $result.Content | ConvertFrom-Json
    Write-Host "   Response sample: $($response.response.Substring(0, 50))..." -ForegroundColor Green
} catch {
    Write-Host "   FAIL - Model not responding" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "3. Testing Aider..." -ForegroundColor Yellow
try {
    aider --version
    Write-Host "   OK - Aider is installed" -ForegroundColor Green
} catch {
    Write-Host "   FAIL - Aider not found. Install with: pip install aider-chat" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "4. Testing Continue integration..." -ForegroundColor Yellow
Write-Host "   INFO - Continue extension must be installed in VS Code" -ForegroundColor Cyan
Write-Host "   INFO - Config should point to: http://localhost:11434" -ForegroundColor Cyan

Write-Host ""
Write-Host "SUCCESS - All systems ready!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Install Continue extension in VS Code"
Write-Host "2. Configure Continue to use Ollama model"
Write-Host "3. Run aider in terminal: aider"
