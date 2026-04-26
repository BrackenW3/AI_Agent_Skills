# i9 Ollama Setup - RTX4080 optimized models
# Run from PS7: .\i9_ollama_setup.ps1

$MODELS_DIR = "D:\Ollama\models"  # Use D: drive or external SSD if available
if (-not (Test-Path $MODELS_DIR)) { New-Item -ItemType Directory -Path $MODELS_DIR -Force }

# Set Ollama to use external drive
[Environment]::SetEnvironmentVariable("OLLAMA_MODELS", $MODELS_DIR, "User")
$env:OLLAMA_MODELS = $MODELS_DIR

Write-Host "=== i9 RTX4080 Ollama Model Setup ===" -ForegroundColor Cyan
Write-Host "Models dir: $MODELS_DIR"
Write-Host "GPU: RTX4080 (16GB VRAM) - can run 70B models quantized"

# Start Ollama if not running  
if (-not (Get-Process ollama -ErrorAction SilentlyContinue)) {
    Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep 3
}

Write-Host "`n--- Embedding ---" -ForegroundColor Yellow
ollama pull nomic-embed-text

Write-Host "`n--- Fast models ---" -ForegroundColor Yellow
ollama pull qwen2.5:7b
ollama pull qwen2.5-coder:7b

Write-Host "`n--- Quality models (RTX4080 handles these well) ---" -ForegroundColor Yellow
ollama pull qwen3:8b
ollama pull deepseek-r1:8b
ollama pull qwen2.5-coder:14b

Write-Host "`n--- Heavy models (RTX4080 16GB can handle these) ---" -ForegroundColor Yellow
ollama pull qwen2.5:32b-instruct-q4_K_M    # 32B quantized, fits in 16GB VRAM
ollama pull qwen2.5-coder:32b-instruct-q4_K_M  # 32B coder
ollama pull deepseek-r1:32b                 # Strong reasoning

Write-Host "`n--- Vision/Multimodal ---" -ForegroundColor Yellow
ollama pull llava:13b                       # Vision model
ollama pull qwen2.5vl:7b                   # Qwen vision

Write-Host "`n=== Done ===" -ForegroundColor Green
Write-Host "Test: ollama run qwen2.5:32b-instruct-q4_K_M 'Hello'"
Write-Host "Models saved to: $MODELS_DIR"
