Option Explicit

Dim shell, fso, scriptDir, supervisor, command
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
supervisor = fso.BuildPath(scriptDir, "warlock-supervisor.ps1")
command = "powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & supervisor & """"

shell.Run command, 0, False
