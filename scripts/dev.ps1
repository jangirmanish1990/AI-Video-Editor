# Launches the backend (uvicorn) and frontend (vite) dev servers.
# Uses the venv Python explicitly so Windows Store Python can never
# shadow it and cause stale-server issues.
$root = Split-Path $PSScriptRoot -Parent
$python = "$root\venv\Scripts\python.exe"

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$root'; '$python' -m uvicorn backend.main:app --reload"
)

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$root\frontend'; npm run dev"
)

Write-Host "Backend  -> http://localhost:8000  (docs at /docs)"
Write-Host "Frontend -> http://localhost:5173"
Write-Host "Python   -> $python"
