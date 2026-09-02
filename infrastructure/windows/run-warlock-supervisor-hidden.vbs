Option Explicit

Dim shell, fso, scriptDir, projectRoot, supervisor, runtimeDir, logFile, stdoutFile, stderrFile, command, exitCode
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
projectRoot = fso.GetParentFolderName(fso.GetParentFolderName(scriptDir))
supervisor = fso.BuildPath(scriptDir, "warlock-supervisor.ps1")
runtimeDir = fso.BuildPath(projectRoot, ".warlock\runtime")
logFile = fso.BuildPath(runtimeDir, "bootstrap.log")
stdoutFile = fso.BuildPath(runtimeDir, "supervisor-bootstrap.out.log")
stderrFile = fso.BuildPath(runtimeDir, "supervisor-bootstrap.err.log")

If Not fso.FolderExists(fso.BuildPath(projectRoot, ".warlock")) Then
    fso.CreateFolder(fso.BuildPath(projectRoot, ".warlock"))
End If
If Not fso.FolderExists(runtimeDir) Then
    fso.CreateFolder(runtimeDir)
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

command = "cmd.exe /d /s /c ""powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & supervisor & """ 1>>""" & stdoutFile & """ 2>>""" & stderrFile & """"""
exitCode = shell.Run(command, 0, True)

If Err.Number <> 0 Then
    LogMessage "Failed to launch supervisor: " & Err.Description
    Err.Clear
Else
    LogMessage "Supervisor process exited with code " & CStr(exitCode) & "."
End If
On Error GoTo 0
