# Launches the backend (uvicorn) and frontend (vite) dev servers, each in its
# own PowerShell window. Run from anywhere:  .\scripts\dev.ps1
$root = Split-Path $PSScriptRoot -Parent

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$root'; .\venv\Scripts\Activate.ps1; python -m uvicorn backend.main:app --reload"
)

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$root\frontend'; npm run dev"
)

Write-Host "Backend  -> http://localhost:8000  (docs at /docs)"
Write-Host "Frontend -> http://localhost:5173"
