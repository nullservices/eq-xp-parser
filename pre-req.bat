@echo off

:: Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed. Please install Python and try again.
    exit /b 1
)

:: Create a virtual environment
python -m venv env

:: Activate the virtual environment
call env\Scripts\activate

:: Install the required dependencies
pip install pillow

:: Check if tkinter is installed
python -c "import tkinter" >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo tkinter is not installed. Please install tkinter manually.
)

:: Deactivate the virtual environment
deactivate

echo Dependencies installed successfully. To activate the virtual environment, run 'env\Scripts\activate'.
