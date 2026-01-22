@echo off
echo ===========================================
echo   Building Desktop Application ( .exe )
echo ===========================================

echo.
echo [1/3] Installing PyInstaller...
pip install pyinstaller

echo.
echo [2/3] Cleaning previous builds...
rmdir /s /q build
rmdir /s /q dist
del *.spec

echo.
echo [3/3] Generating Executable...
echo This might take a minute...

pyinstaller --noconfirm --onefile --windowed --name "Inventory Manager" ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --hidden-import "reportlab" ^
    --hidden-import "reportlab.platypus" ^
    --hidden-import "reportlab.lib.styles" ^
    --hidden-import "uuid" ^
    --hidden-import "sqlite3" ^
    launcher.py

echo.
echo ===========================================
echo   BUILD COMPLETE!
echo ===========================================
echo.
echo You can find your app here:
echo   dist\Inventory Manager.exe
echo.
pause
