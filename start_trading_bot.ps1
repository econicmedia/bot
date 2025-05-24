#!/usr/bin/env powershell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    AI Trading Bot - Quick Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Checking environment..." -ForegroundColor Yellow

if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please ensure venv is set up correctly." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Virtual environment found: OK" -ForegroundColor Green
Write-Host ""

Write-Host "Starting AI Trading Bot Server..." -ForegroundColor Yellow
Write-Host "Dashboard will be available at: " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8080/dashboard" -ForegroundColor Cyan
Write-Host "API docs will be available at: " -NoNewline -ForegroundColor White  
Write-Host "http://localhost:8080/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

try {
    & "venv\Scripts\python.exe" "main_server_fixed.py"
}
catch {
    Write-Host "Error starting server: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Server stopped." -ForegroundColor Yellow
Read-Host "Press Enter to exit"
