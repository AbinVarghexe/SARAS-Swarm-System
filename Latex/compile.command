#!/usr/bin/env bash
# macOS Finder Double-Clickable Compiler Script
cd "$(dirname "$0")/Report_format_S7" || exit 1
echo "==================================================="
echo "  Compiling KTU S7 Seminar Report on macOS..."
echo "==================================================="
if command -v python3 >/dev/null 2>&1; then
    python3 compile_report.py Main.tex
elif command -v python >/dev/null 2>&1; then
    python compile_report.py Main.tex
else
    echo "[-] Error: Python is not installed. Please install Python 3."
fi
echo ""
echo "==================================================="
echo "  Done! Check Main.pdf inside Report_format_S7"
echo "==================================================="
read -n 1 -s -r -p "Press any key to close..."
