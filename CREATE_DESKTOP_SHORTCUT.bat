@echo off
title Create Desktop Shortcut - Local AI Model Manager
color 0B

echo ===================================================
echo   🤖 CREATE DESKTOP SHORTCUT - AI MODEL MANAGER
echo ===================================================
echo.

REM Get current directory
set "SCRIPT_DIR=%~dp0"

REM Target icon path
set "ICON_LOCATION=%SCRIPT_DIR%ai_model_stylish.ico"

if not exist "%ICON_LOCATION%" (
    set "ICON_LOCATION=%SystemRoot%\System32\shell32.dll,138"
)

REM Create VBScript to create shortcut in multiple desktop folders
set "VBS_FILE=%TEMP%\create_ai_shortcut.vbs"

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBS_FILE%"
echo Set fso = CreateObject("Scripting.FileSystemObject") >> "%VBS_FILE%"
echo userProfile = oWS.ExpandEnvironmentStrings("%%USERPROFILE%%") >> "%VBS_FILE%"
echo. >> "%VBS_FILE%"
echo Sub CreateLink(sLinkFile) >> "%VBS_FILE%"
echo     On Error Resume Next >> "%VBS_FILE%"
echo     If fso.FolderExists(fso.GetParentFolderName(sLinkFile)) Then >> "%VBS_FILE%"
echo         If fso.FileExists(sLinkFile) Then fso.DeleteFile sLinkFile, True >> "%VBS_FILE%"
echo         Set oLink = oWS.CreateShortcut(sLinkFile) >> "%VBS_FILE%"
echo         oLink.TargetPath = "%SCRIPT_DIR%Launch_AI_Model_Manager.bat" >> "%VBS_FILE%"
echo         oLink.WorkingDirectory = "%SCRIPT_DIR%" >> "%VBS_FILE%"
echo         oLink.IconLocation = "%ICON_LOCATION%,0" >> "%VBS_FILE%"
echo         oLink.Description = "Local AI Model Manager - Ollama Resource Orchestrator" >> "%VBS_FILE%"
echo         oLink.Save >> "%VBS_FILE%"
echo         WScript.Echo "Created shortcut at: " ^& sLinkFile >> "%VBS_FILE%"
echo     End If >> "%VBS_FILE%"
echo End Sub >> "%VBS_FILE%"
echo. >> "%VBS_FILE%"
echo ' Create links in standard, local, and OneDrive Desktop folders >> "%VBS_FILE%"
echo CreateLink oWS.SpecialFolders("Desktop") ^& "\Local AI Model Manager.lnk" >> "%VBS_FILE%"
echo CreateLink userProfile ^& "\Desktop\Local AI Model Manager.lnk" >> "%VBS_FILE%"
echo CreateLink userProfile ^& "\OneDrive\Desktop\Local AI Model Manager.lnk" >> "%VBS_FILE%"

REM Run VBScript
cscript //nologo "%VBS_FILE%"

REM Clean up
del "%VBS_FILE%"

REM Refresh Explorer icon cache
if exist "%SystemRoot%\System32\ie4uinit.exe" "%SystemRoot%\System32\ie4uinit.exe" -show >nul 2>&1

echo.
echo ===================================================
echo   🎉 SUCCESS!
echo ===================================================
echo.
echo Desktop shortcut created with custom premium icon!
echo.
echo Double-click "Local AI Model Manager" on your 
echo desktop to start the application.
echo.
echo ===================================================
echo.
pause
