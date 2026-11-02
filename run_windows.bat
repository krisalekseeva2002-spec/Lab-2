@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if errorlevel 1 goto folder_error

echo HotelDoc AI - Windows launcher
echo.
echo Checking Python version...
set "PY_CMD="
where py >nul 2>&1
if not errorlevel 1 (
    for %%V in (3.14 3.13 3.12 3.11) do (
        if not defined PY_CMD (
            py -%%V -c "import sys" >nul 2>&1
            if not errorlevel 1 set "PY_CMD=py -%%V"
        )
    )
)
if not defined PY_CMD (
    where python >nul 2>&1
    if not errorlevel 1 (
        python -c "import sys; raise SystemExit(not ((3,11) <= sys.version_info[:2] <= (3,14)))" >nul 2>&1
        if not errorlevel 1 set "PY_CMD=python"
    )
)
if not defined PY_CMD goto missing_python

echo Using %PY_CMD%
%PY_CMD% --version
if errorlevel 1 goto missing_python

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo Creating virtual environment...
    %PY_CMD% -m venv ".venv"
    if errorlevel 1 goto venv_error
)
if not exist ".venv\Scripts\python.exe" goto venv_error

".venv\Scripts\python.exe" -c "import sys; raise SystemExit(not ((3,11) <= sys.version_info[:2] <= (3,14)))"
if errorlevel 1 goto incompatible_venv

echo.
echo Updating pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto install_error

echo.
echo Installing CPU-only PyTorch and torchvision...
".venv\Scripts\python.exe" -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 goto install_error

echo.
echo Installing HotelDoc AI dependencies...
".venv\Scripts\python.exe" -m pip install -r "requirements.txt"
if errorlevel 1 goto install_error

echo.
echo Starting HotelDoc AI at http://localhost:8501
echo To stop the server, press Ctrl+C.
".venv\Scripts\python.exe" -m streamlit run "app.py" --server.address 127.0.0.1
if errorlevel 1 goto launch_error
goto end

:folder_error
echo ERROR: Cannot open the project folder.
goto failure

:missing_python
echo ERROR: Python 3.11, 3.12, 3.13 or 3.14 was not detected.
echo Verify installation with: py -0p
echo Or check with: python --version
goto failure

:incompatible_venv
echo ERROR: Existing .venv has an unsupported Python version.
echo Rename the .venv folder to .venv_old and start this script again.
goto failure

:venv_error
echo ERROR: Failed to create the Python virtual environment.
goto failure

:install_error
echo ERROR: Installation failed. Read the pip error message above.
echo If a package has no Python 3.14 wheel, try Python 3.12.
goto failure

:launch_error
echo ERROR: Streamlit failed to start. Read the messages above.
goto failure

:failure
echo.
pause
exit /b 1

:end
echo.
echo HotelDoc AI stopped.
pause
endlocal
