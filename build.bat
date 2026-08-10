@echo off
rem build.bat - PyInstaller Batch Compilation Script for Dienstplane System

echo ================================================
echo  Building Dienstplane Executable with PyInstaller
echo ================================================

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

pyinstaller --noconfirm ^
    --onefile ^
    --windowed ^
    --name "Dienstplane" ^
    --add-data "web;web" ^
    --collect-all "customtkinter" ^
    --collect-all "ortools" ^
    --hidden-import "flask" ^
    --hidden-import "flask_cors" ^
    --hidden-import "docx" ^
    --hidden-import "reportlab" ^
    --hidden-import "win32com" ^
    --hidden-import "jinja2" ^
    --hidden-import "werkzeug" ^
    --hidden-import "sqlite3" ^
    main.py

echo.
echo ================================================
echo  Build Complete! Executable saved in dist\Dienstplane.exe
echo ================================================
pause


