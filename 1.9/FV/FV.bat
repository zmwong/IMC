@echo off
REM filepath: c:\FV_tools\IMC_Tool\FV\FV.bat

REM Get the directory where this batch file is located
set "CURDIR=%~dp0"
REM Go up one level to IMC_Tool_v1.9
set "IMCROOT=%CURDIR%..\"


REM Default time_to_execute in seconds (3 hours)
set "TIME_SEC=10800"

REM Parse arguments
:parse
if "%~1"=="" goto run
if /i "%~1"=="-t" (
    set /a TIME_SEC=%2*60
    shift
    shift
    goto parse
)
shift
goto parse

:run
pushd "%CURDIR%"
python "%IMCROOT%runIMC.py" MI_test.xml -m 100 --stop-on-error --time_to_execute %TIME_SEC%
popd