@echo off
setlocal
cd /d "%~dp0"

set "GRADLE_USER_HOME=%~dp0.i10-gradle-user-home"
if not exist "%GRADLE_USER_HOME%" mkdir "%GRADLE_USER_HOME%"

if not exist "I10-SOURCE-COMMIT.txt" (
  echo ERROR: I10-SOURCE-COMMIT.txt is missing.
  pause
  exit /b 1
)

echo Starting I10 Client B manually...
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 run-i10-manual-process.py client-b
) else (
  python run-i10-manual-process.py client-b
)
set "I10_EXIT=%ERRORLEVEL%"
if not "%I10_EXIT%"=="0" echo ERROR: I10 Client B exited with code %I10_EXIT%.
pause
exit /b %I10_EXIT%
