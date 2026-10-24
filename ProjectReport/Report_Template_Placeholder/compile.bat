@echo off
echo ========================================================
echo   Compiling KTU B.Tech Project Report...
echo ========================================================
cd /d "%~dp0"
python compile_report.py main.tex
echo.
echo ========================================================
echo   Finished! Check main.pdf
echo ========================================================
pause
