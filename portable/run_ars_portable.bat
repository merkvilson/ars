@echo off
setlocal

rem Run ARS using a bundled python_embeded (ComfyUI-style portable layout).
set "ROOT=%~dp0.."
set "PYROOT=%ROOT%\python_embeded"
set "PY=%PYROOT%\python.exe"
set "MAIN=%ROOT%\main.py"
set "LOG=%ROOT%\portable\portable_run.log"

if not exist "%PY%" (
  echo [ERROR] python_embeded not found.
  echo Expected: %PY%
  echo.
  echo Build it first:
  echo   powershell -ExecutionPolicy Bypass -File portable\build_portable.ps1
  goto :fail
)

if not exist "%MAIN%" (
  echo [ERROR] main.py not found: %MAIN%
  goto :fail
)

rem Ensure relative paths (res/, theme/, etc.) resolve correctly when launching by double-click.
pushd "%ROOT%" >nul

rem Help DLL discovery for packages like PyQt6 (Qt DLLs) if present.
if exist "%PYROOT%\Lib\site-packages\PyQt6\Qt6\bin" (
  set "PATH=%PYROOT%\Lib\site-packages\PyQt6\Qt6\bin;%PATH%"
)
set "PATH=%PYROOT%;%PYROOT%\Scripts;%PATH%"

rem Enable this if you want full tracebacks in the log:
rem set "ARS_SHOW_STDERR=1"

"%PY%" -u "%MAIN%" %* 1>>"%LOG%" 2>>&1

popd >nul

if errorlevel 1 (
  echo.
  echo [ERROR] ARS exited with errorlevel %errorlevel%
  echo Log: %LOG%
  goto :fail
)

endlocal
goto :eof

:fail
echo.
pause
endlocal
exit /b 1
