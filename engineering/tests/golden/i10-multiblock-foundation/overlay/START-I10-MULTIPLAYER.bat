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

set "I10_COMMIT="
for /f "usebackq delims=" %%S in ("I10-SOURCE-COMMIT.txt") do if not defined I10_COMMIT set "I10_COMMIT=%%S"
if not defined I10_COMMIT (
  echo ERROR: I10-SOURCE-COMMIT.txt is empty.
  pause
  exit /b 1
)

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 run-i10-multiplayer-acceptance.py --commit "%I10_COMMIT%"
) else (
  python run-i10-multiplayer-acceptance.py --commit "%I10_COMMIT%"
)
set "I10_EXIT=%ERRORLEVEL%"
if not "%I10_EXIT%"=="0" (
  echo.
  echo ERROR: I10 multiplayer launcher failed with exit code %I10_EXIT%.
  echo Full Gradle diagnostics are preserved under build\i10-multiplayer-acceptance\.
)
pause
exit /b %I10_EXIT%
