# Start Aider coding agent with local Ollama model

# This script starts Aider in interactive mode with the Qwen2.5-Coder model

Write-Host "🤖 Starting Aider with local Qwen2.5-Coder model..." -ForegroundColor Green
Write-Host "Ollama endpoint: http://localhost:11434" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tips:" -ForegroundColor Yellow
Write-Host "  - Type your request like: 'add logging to all python files'"
Write-Host "  - Type 'help' for commands"
Write-Host "  - Type '/exit' to quit"
Write-Host ""

aider --model ollama/qwen2.5-coder:14b
