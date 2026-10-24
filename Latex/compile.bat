@echo off
echo ===================================================
echo   Compiling KTU S7 Seminar Report...
echo ===================================================
cd /d "%~dp0\Report_format_S7"
python compile_report.py Main.tex
echo.
echo ===================================================
echo   Finished! Check Main.pdf
echo ===================================================
pause
