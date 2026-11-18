@echo off
REM Genera dist\csv-a-word.exe (hay que ejecutarlo en Windows). La ventana NO se cierra sola: deja el resultado en build.log.
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set LOG=build.log
echo Construyendo... (detalle en %LOG%)
echo. > %LOG%

REM 1) Buscar Python: primero el lanzador "py", luego "python".
set PY=
py -3.13 --version >nul 2>&1 && set PY=py -3.13
if not defined PY python --version >nul 2>&1 && set PY=python
if not defined PY (
    echo [ERROR] No se encontro Python. Instalalo desde https://www.python.org/downloads/ marcando "Add python.exe to PATH".
    goto :fin
)
echo Usando: %PY%

REM 2) Entorno virtual y dependencias.
if not exist .venv\Scripts\python.exe (
    %PY% -m venv .venv >> %LOG% 2>&1 || goto :error
)
set VPY=.venv\Scripts\python.exe
%VPY% -m pip install --upgrade pip >> %LOG% 2>&1 || goto :error
%VPY% -m pip install -r requirements-dev.txt >> %LOG% 2>&1 || goto :error

REM 3) Pruebas.
%VPY% -m unittest discover -s tests -t . >> %LOG% 2>&1 || goto :error

REM 4) .exe. Para ver errores en pantalla al usarlo, quita --windowed.
%VPY% -m PyInstaller --noconfirm --clean --onefile --windowed --name csv-a-word --collect-data docx run.py >> %LOG% 2>&1 || goto :error

echo.
echo Listo: dist\csv-a-word.exe
goto :fin

:error
echo.
echo [ERROR] Fallo la construccion. Abre %LOG% y busca la ultima linea con "Error".

:fin
echo.
pause
