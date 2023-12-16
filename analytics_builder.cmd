@echo off

rem Copyright (c) 2019 Software AG, Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA, and/or its subsidiaries and/or its affiliates and/or their licensors.
rem Use, reproduction, transfer, publication or disclosure is prohibited except as specifically provided for in your License Agreement with Software AG

setlocal

set THIS_SCRIPT=%~$PATH:0
call :getpath %THIS_SCRIPT
set "PATH=%APAMA_HOME%\third_party\python;%PATH%"

set PYTHON_VERSION=0
for /f %%i in ('python -c "import sys; print(sys.version_info[0])"') do set PYTHON_VERSION=%%i
if %PYTHON_VERSION% LSS 3 (goto PY_UNDEFINED)

python.exe "%THIS_DIR%/analytics_builder" %* || EXIT /B 1
goto END

:PY_UNDEFINED
echo Add an appropriate Python 3 version to your path. Refer to the system requirements in the README of the Analytics Builder Block SDK documentation.
goto END

:END
endlocal
exit /b

:getpath
set THIS_DIR=%~dp0
exit /b