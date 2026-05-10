param(
    [string]$Port = "8000",
    [switch]$NoBrowser
)

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ProjectRoot "backend"
$LogFile = Join-Path $ProjectRoot "server.log"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VG 24H - Portal de Servicos Publicos" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Mata processos antigos na porta
$listeners = netstat -ano | Select-String ":$Port"
foreach ($line in $listeners) {
    if ($line -match '\s+(\d+)$') {
        Stop-Process -Id $matches[1] -Force -ErrorAction SilentlyContinue
    }
}
Start-Sleep 1

"--- Servidor iniciado em $(Get-Date) ---" | Out-File $LogFile -Encoding UTF8

# Inicia o servidor Django como processo independente
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "uv"
$psi.Arguments = "run --project . python manage.py runserver 0.0.0.0:$Port --noreload"
$psi.WorkingDirectory = $BackendDir
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.CreateNoWindow = $true

$proc = [System.Diagnostics.Process]::Start($psi)

# Le a saida em tempo real procurando a mensagem de startup
$reader = $proc.StandardOutput
$timeout = 30
$started = $false

Write-Host "Aguardando servidor iniciar" -NoNewline

while ($timeout -gt 0) {
    $line = $reader.ReadLine()
    if ($line -ne $null) {
        Add-Content $LogFile $line -Encoding UTF8
        if ($line -like "*Starting development server*") {
            $started = $true
            Write-Host " OK!" -ForegroundColor Green
            break
        }
    } else {
        Write-Host "." -NoNewline
        Start-Sleep 1
        $timeout--
    }
}

# Le o restante da saida em background
Start-Job -Name "vg24h_log" -ScriptBlock {
    param($r, $log)
    while (-not $r.EndOfStream) {
        $l = $r.ReadLine()
        if ($l) { Add-Content $log $l -Encoding UTF8 }
    }
} -ArgumentList $reader, $LogFile | Out-Null

if (-not $started) {
    Write-Host " TIMEOUT" -ForegroundColor Red
    Write-Host "Verifique o log: $LogFile" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Servidor rodando em: http://127.0.0.1:$Port/" -ForegroundColor Green
Write-Host "Log: $LogFile" -ForegroundColor DarkGray
Write-Host ""

if (-not $NoBrowser) {
    Start-Process "http://127.0.0.1:$Port/"
}

Write-Host "Para parar o servidor, feche este terminal ou pressione Ctrl+C" -ForegroundColor Yellow
Write-Host ""

# Mantem o script rodando (para o servidor nao morrer)
while ($true) {
    Start-Sleep 10
    if ($proc.HasExited) {
        Write-Host "Servidor encerrado." -ForegroundColor Red
        break
    }
}
