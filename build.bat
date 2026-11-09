@echo off
REM ============================================================
REM  Compila el Cotizador de Ventanas de Aluminio a un .exe
REM  Resultado: dist\CotizadorVentanas.exe
REM ============================================================
cd /d "%~dp0"

echo [1/3] Instalando dependencias...
python -m pip install -r requirements-dev.txt || goto :error

echo [2/3] Ejecutando pruebas...
python -m pytest -q || goto :error

echo [3/3] Compilando ejecutable...
python -m PyInstaller --noconsole --onefile --clean --name "CotizadorVentanas" --collect-data customtkinter main.py || goto :error

echo.
echo Listo. Ejecutable generado en: dist\CotizadorVentanas.exe
pause
exit /b 0

:error
echo.
echo Ocurrio un error. Revisa los mensajes anteriores.
pause
exit /b 1
