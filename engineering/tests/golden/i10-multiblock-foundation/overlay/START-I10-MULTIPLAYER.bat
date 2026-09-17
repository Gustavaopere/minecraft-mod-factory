@echo off
setlocal
cd /d "%~dp0"

if not exist "I10-SOURCE-COMMIT.txt" (
  echo ERROR: I10-SOURCE-COMMIT.txt is missing.
  exit /b 1
)

set "I10_COMMIT="
for /f "usebackq delims=" %%S in ("I10-SOURCE-COMMIT.txt") do if not defined I10_COMMIT set "I10_COMMIT=%%S"
if not defined I10_COMMIT (
  echo ERROR: I10-SOURCE-COMMIT.txt is empty.
  exit /b 1
)

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 run-i10-multiplayer-acceptance.py --commit "%I10_COMMIT%"
) else (
  python run-i10-multiplayer-acceptance.py --commit "%I10_COMMIT%"
)
set "I10_EXIT=%ERRORLEVEL%"
pause
exit /b %I10_EXIT%
