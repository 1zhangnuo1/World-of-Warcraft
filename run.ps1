$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "Install uv first: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
}
& uv sync --locked
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& uv run --frozen navigation-lab @args
exit $LASTEXITCODE
