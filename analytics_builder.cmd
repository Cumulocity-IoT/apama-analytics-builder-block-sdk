@echo off

rem Copyright (c) 2019 Software AG, Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA, and/or its subsidiaries and/or its affiliates and/or their licensors.
rem Use, reproduction, transfer, publication or disclosure is prohibited except as specifically provided for in your License Agreement with Software AG

setlocal

if not defined APAMA_HOME (goto UNDEFINED)

set THIS_SCRIPT=%~$PATH:0
call :getpath %THIS_SCRIPT
set "PATH=%APAMA_HOME%\third_party\python;%PATH%"
python.exe "%THIS_DIR%/analytics_builder" %* || EXIT /B 1
goto END

:UNDEFINED
echo Please run this script from an apama_env shell or Apama Command Prompt.
goto END

:END
endlocal
exit /b

:getpath
set THIS_DIR=%~dp0
exit /b