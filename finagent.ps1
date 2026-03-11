# finagent.ps1 - Interactive with Menu

# 1. Prompt for Symbol
$symbol = Read-Host "Enter stock symbol (e.g., GOOG)"
if ([string]::IsNullOrWhiteSpace($symbol)) {
    Write-Host "Error: Symbol cannot be empty." -ForegroundColor Red
    Pause; exit 1
}

# 2. Selectable Menu for Period
Write-Host "`nSelect Period:" -ForegroundColor Cyan
Write-Host "1) short+ (within 2 weeks)"
Write-Host "2) short  (2 weeks to 1 month)"
Write-Host "3) medium (1 month to 1 year)"
Write-Host "4) long   (1 year to 2 years)"

$choice = Read-Host "`nEnter option [1-4]"

# Map selection to argument
switch ($choice) {
    "1" { $period = "short+" }
    "2" { $period = "short" }
    "3" { $period = "medium" }
    "4" { $period = "long" }
    Default { 
        Write-Host "Invalid selection. Exiting." -ForegroundColor Red
        Pause; exit 1 
    }
}

# 3. Activate environment and run
Write-Host "`nActivating conda environment..." -ForegroundColor DarkGray
conda activate finagent
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Run setup.cmd first to create 'finagent'." -ForegroundColor Yellow
    Pause; exit 1
}

Write-Host "Running finagent for $symbol ($period)...`n" -ForegroundColor Green
python finagent_cli.py --symbol $symbol --period $period

Write-Host "`nFinished."
Pause
