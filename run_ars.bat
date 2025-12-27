@echo off
setlocal

rem Run ARS using the workspace-local virtual environment.
set "ROOT=%~dp0"
set "PY=%ROOT%.venv\Scripts\python.exe"
set "MAIN=%ROOT%main.py"

if not exist "%PY%" (
  echo [ERROR] Virtual environment python not found:
  echo         %PY%
  echo.
  echo Create the venv in .venv, then install requirements.
  echo Example:
  echo   py -m venv .venv
  echo   .venv\Scripts\python -m pip install -r requirements.txt
  goto :fail
)

if not exist "%MAIN%" (
  echo [ERROR] main.py not found:
  echo         %MAIN%
  goto :fail
)

"%PY%" "%MAIN%" %*

if errorlevel 1 (
  echo.
  echo [ERROR] main.py exited with errorlevel %errorlevel%
  goto :fail
)

endlocal

goto :eof

:fail
echo.
pause
endlocal
exit /b 1
