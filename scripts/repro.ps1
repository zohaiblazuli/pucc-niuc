# Reproducible benchmarking script for PCC-NIUC I²-Bench-Lite (PowerShell)
# Compares baseline (no gate) vs block vs rewrite modes
param(
    [string]$ModelType = "mock",
    [string]$ScenariosFile = "bench/scenarios.jsonl",
    [string]$ResultsDir = "results"
)

Write-Host "🔒 PCC-NIUC I²-Bench-Lite Reproducible Evaluation" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "This script runs comprehensive benchmarks comparing:"
Write-Host "  • Baseline (no gate) - unprotected model responses"
Write-Host "  • Block mode - strict violation blocking"  
Write-Host "  • Rewrite mode - neutralization with re-verification"
Write-Host

# Configuration
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "📋 Configuration:" -ForegroundColor Yellow
Write-Host "  Model type: $ModelType"
Write-Host "  Scenarios: $ScenariosFile"
Write-Host "  Results dir: $ResultsDir"
Write-Host "  Timestamp: $Timestamp"
Write-Host

# Check Python
Write-Host "🔧 Environment Check:" -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Python: ✅ $pythonVersion"
} catch {
    Write-Host "  Python: ❌ Not found" -ForegroundColor Red
    exit 1
}

# Clean previous results
Write-Host "🧹 Cleaning previous results..." -ForegroundColor Yellow
if (Test-Path $ResultsDir) {
    Remove-Item -Recurse -Force $ResultsDir
}
New-Item -ItemType Directory -Path $ResultsDir -Force | Out-Null
Write-Host "  Results directory: ✅"

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
try {
    pip install -e . | Out-Null
    Write-Host "  Dependencies: ✅"
} catch {
    Write-Host "  Dependencies: ⚠️ Warning - pip install had issues" -ForegroundColor Yellow
}

# Verify scenarios file
if (-not (Test-Path $ScenariosFile)) {
    Write-Host "❌ Scenarios file not found: $ScenariosFile" -ForegroundColor Red
    exit 1
}

$scenarioCount = (Get-Content $ScenariosFile | Measure-Object -Line).Lines
Write-Host "  Scenarios file: ✅ ($scenarioCount scenarios)"
Write-Host

# Run the Python evaluation
Write-Host "🧪 Running I²-Bench-Lite Comprehensive Evaluation..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

try {
    python scripts/run_benchmarks.py --model $ModelType --scenarios $ScenariosFile --results-dir $ResultsDir --timestamp $Timestamp
    $exitCode = $LASTEXITCODE
} catch {
    Write-Host "❌ Benchmark execution failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host
Write-Host "🎯 Evaluation complete! Check $ResultsDir/ directory for outputs." -ForegroundColor Green
Write-Host "📊 Key files generated:" -ForegroundColor Green
Write-Host "  • $ResultsDir/metrics_$Timestamp.csv - Detailed scenario results"
Write-Host "  • $ResultsDir/summary_$Timestamp.md - Executive summary with tables"
Write-Host
Write-Host "💡 To run with different model:" -ForegroundColor Blue
Write-Host "  .\scripts\repro.ps1 -ModelType api"
Write-Host "  .\scripts\repro.ps1 -ModelType local"
Write-Host
Write-Host "🔍 Next steps:" -ForegroundColor Blue
Write-Host "  • Review $ResultsDir/summary_*.md for research insights"
Write-Host "  • Analyze $ResultsDir/metrics_*.csv for detailed breakdown"
Write-Host "  • Compare performance across different model types"

exit $exitCode
