#!/usr/bin/env bash
# KTU S7 Seminar Report 1-Click Compiler for macOS and Linux
cd "$(dirname "$0")/Report_format_S7" || exit 1
if command -v python3 >/dev/null 2>&1; then
    python3 compile_report.py Main.tex
elif command -v python >/dev/null 2>&1; then
    python compile_report.py Main.tex
else
    echo "[-] Error: Python is not installed. Please install Python 3."
    exit 1
fi
