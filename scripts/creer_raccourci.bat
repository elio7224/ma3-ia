@echo off
:: Cree le raccourci "MA3-IA" sur le Bureau (icone MA3-IA, aucune fenetre noire au lancement).
cd /d "%~dp0.."
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$d = [Environment]::GetFolderPath('Desktop'); $s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $d 'MA3-IA.lnk'));" ^
  "$s.TargetPath = (Resolve-Path 'venv\Scripts\pythonw.exe').Path; $s.Arguments = 'ma3ia\desktop.py';" ^
  "$s.WorkingDirectory = (Get-Location).Path; $s.IconLocation = (Resolve-Path 'ma3ia\assets\ma3ia.ico').Path + ',0';" ^
  "$s.Description = 'grandMA3 AI Control'; $s.Save()"
if /i not "%~1"=="silencieux" (
    echo Raccourci "MA3-IA" cree sur le Bureau.
    pause
)
