# Start Aider in autonomous mode (Windsurf-style)

# This enables fully autonomous editing with auto-commits
# WARNING: This will auto-edit files without confirmation. Use with caution!

Write-Host "🚀 Starting Aider in AUTONOMOUS mode..." -ForegroundColor Cyan
Write-Host "This will:" -ForegroundColor Yellow
Write-Host "  ✓ Auto-edit files"
Write-Host "  ✓ Auto-commit changes"
Write-Host "  ✓ Loop until task complete"
Write-Host ""
Write-Host "Example commands:" -ForegroundColor Green
Write-Host '  aider> refactor this project to add type hints'
Write-Host '  aider> fix all linting issues'
Write-Host '  aider> add docstrings to all functions'
Write-Host ""

aider --model ollama/qwen2.5-coder:14b --yes --auto-commits
