@echo off

REM Check if both IP address and token are provided as parameters
IF "%~1"=="" (
    echo IP address is missing.
    exit /b
)
IF "%~2"=="" (
    echo Token is missing.
    exit /b
)

REM Set the parameters to variables
SET ipAddress=%~1
SET token=%~2

REM Construct the curl command
SET curlCommand=curl -G "http://%ipAddress%:8080" --data-urlencode "url=https://www.forestapp.cc/join-room?token=%token%"

REM Create a temporary VBScript file
echo Set objShell = WScript.CreateObject("WScript.Shell") > %temp%\runhidden.vbs
echo objShell.Run "%curlCommand%", 0 >> %temp%\runhidden.vbs

REM Execute the VBScript file to run the curl command silently
cscript //nologo %temp%\runhidden.vbs

REM Delete the temporary VBScript file
del %temp%\runhidden.vbs

REM Exit the batch file
exit /b
