# powershell
# sample command: .\finagent.ps1 GLD short

# Check if exactly 2 arguments are provided
if ($args.Count -lt 2) {
    if (-not $args[0]) {
        Write-Host "Missing stock symbol (e.g., GOOG)."
    }
    if (-not $args[1]) {
        Write-Host "Missing period ('short+' within 2 weeks; 'short' from 2 weeks to 1 month; 'medium' from 1 month to 1 year; 'long' from 1 year to 2 years)."
    }
    exit 1
}

# Activate conda environment
conda activate finagent
if ($LASTEXITCODE -ne 0) {
    Write-Host "Please run setup.cmd first to create the environment - finagent."
    exit 1
}

# Run the Python script with the provided arguments
python finagent_cli.py --symbol $args[0] --period $args[1]