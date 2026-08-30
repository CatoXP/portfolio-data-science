# Crea el acceso directo del Escritorio con su icono.
# Uso:  powershell -ExecutionPolicy Bypass -File crear_acceso_directo.ps1

$proyecto = Split-Path -Parent $MyInvocation.MyCommand.Path
$icono = Join-Path $proyecto "icono.ico"

# pythonw.exe abre la app sin dejar una ventana de consola detras.
$py = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = (Get-Command python).Source -replace 'python\.exe$', 'pythonw.exe' }
if (-not (Test-Path $py)) { Write-Error "No encontre pythonw.exe"; exit 1 }

if (-not (Test-Path $icono)) {
    Write-Host "Generando el icono..."
    & (Get-Command python).Source (Join-Path $proyecto "generar_icono.py")
}

$escritorio = [Environment]::GetFolderPath('Desktop')
$destino = Join-Path $escritorio "Traductor de Subtitulos.lnk"

$shell = New-Object -ComObject WScript.Shell
$lnk = $shell.CreateShortcut($destino)
$lnk.TargetPath = $py
$lnk.Arguments = "main.py"
$lnk.WorkingDirectory = $proyecto
$lnk.IconLocation = "$icono,0"
$lnk.Description = "Traductor de subtitulos en vivo, ingles a espanol, sin conexion"
$lnk.WindowStyle = 1
$lnk.Save()

Write-Host "Acceso directo creado en: $destino"
