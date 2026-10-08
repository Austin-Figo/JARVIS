$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath('Desktop')
$Shortcut = $WshShell.CreateShortcut("$DesktopPath\JARVIS.lnk")

if (Test-Path "C:\JARVIS\dist\JARVIS\JARVIS.exe") {
    $Shortcut.TargetPath = "C:\JARVIS\dist\JARVIS\JARVIS.exe"
    $Shortcut.WorkingDirectory = "C:\JARVIS\dist\JARVIS"
} else {
    $Shortcut.TargetPath = "C:\JARVIS\run_jarvis.bat"
    $Shortcut.WorkingDirectory = "C:\JARVIS"
    $Shortcut.WindowStyle = 7 # Minimized
}

$Shortcut.Description = "JARVIS AI Assistant"
$Shortcut.Save()
Write-Host "Created Desktop Shortcut: $DesktopPath\JARVIS.lnk"

