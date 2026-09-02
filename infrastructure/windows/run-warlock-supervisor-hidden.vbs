Option Explicit

Dim shell, fso, scriptDir, projectRoot, supervisor, logFile, command
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
projectRoot = fso.GetParentFolderName(fso.GetParentFolderName(scriptDir))
supervisor = fso.BuildPath(scriptDir, "warlock-supervisor.ps1")
logFile = fso.BuildPath(projectRoot, ".warlock\runtime\bootstrap.log")

If Not fso.FolderExists(fso.BuildPath(projectRoot, ".warlock\runtime")) Then
    fso.CreateFolder(fso.BuildPath(projectRoot, ".warlock"))
    fso.CreateFolder(fso.BuildPath(projectRoot, ".warlock\runtime"))
End If

Sub LogMessage(message)
    Dim file
    Set file = fso.OpenTextFile(logFile, 8, True)
    file.WriteLine Now & " | " & message
    file.Close
End Sub

On Error Resume Next
shell.CurrentDirectory = projectRoot
LogMessage "Hidden launcher starting supervisor."
command = "powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & supervisor & """"
shell.Run command, 0, True
If Err.Number <> 0 Then
    LogMessage "Supervisor exited with launcher error: " & Err.Description
    Err.Clear
Else
    LogMessage "Supervisor process exited."
End If
On Error GoTo 0
